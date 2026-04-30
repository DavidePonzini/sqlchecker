'''Detector for semantic errors in SQL queries.'''

import re
from typing import Callable
from sqlglot import exp
from z3 import Not, Or, And
from sql_error_taxonomy import SqlErrors
from sqlscope import util
from sqlscope.query import Query, smt

from .base import BaseDetector, DetectedError

class SemanticErrorDetector(BaseDetector):
    '''Detector for semantic errors in SQL queries.'''
    
    def __init__(self,
                 *,
                 query: Query,
                 update_query: Callable[[str, str | None], None],
                 solutions: list[Query] = [],
                ):
        super().__init__(
            query=query,
            solutions=solutions,
            update_query=update_query,
        )

    def run(self) -> list[DetectedError]:
        results: list[DetectedError] = super().run()

        checks = [
            self.detect_38_tautological_or_inconsistent_expression,
            self.detect_39_distinct_in_sum_or_avg,
            self.detect_40_distinct_removing_important_duplicates,
            self.detect_41_mixing_comparison_and_null,
            self.detect_42_null_in_InAnyAll_subquery,
            self.detect_43_join_condition_on_unmatchable_column,
            self.detect_44_many_duplicates,
            self.detect_45_constant_column_output,
            self.detect_46_duplicate_column_output,
        ]
        
        for chk in checks:
            results.extend(chk())

        return results

    def detect_38_tautological_or_inconsistent_expression(self) -> list[DetectedError]:
        results: list[DetectedError] = []

        for select in self.query.selects:
            where = select.where

            if not where:
                continue

            # Build Z3 variables from catalog
            variables = {}
            for table in select.referenced_tables:
                variables.update(smt.catalog_table_to_z3_vars(table))

            dnf = util.ast.extract_DNF(where)


            # Refer to Brass & Goldberg, 2006 for these checks (error #8)
            # (1) whole formula
            try:
                whole_clauses = [smt.sql_to_z3(C, variables) for C in dnf]
                whole = Or(*whole_clauses)
            except Exception:
                continue  # skip if cannot convert to z3

            if not smt.is_satisfiable(whole):
                results.append(DetectedError(SqlErrors.IMPLIED_TAUTOLOGICAL_OR_INCONSISTENT_EXPRESSION, ('contradiction',)))
            elif not smt.is_satisfiable(Not(whole)):
                results.append(DetectedError(SqlErrors.IMPLIED_TAUTOLOGICAL_OR_INCONSISTENT_EXPRESSION, ('tautology',)))
                
            # (2) each Ci redundant?
            for i, Ci in enumerate(dnf):
                    Ci_z3 = smt.sql_to_z3(Ci, variables)
                    others = Or(*[smt.sql_to_z3(C, variables) for j, C in enumerate(dnf) if j != i])
                    if not smt.is_satisfiable(And(Ci_z3, Not(others))):
                        results.append(DetectedError(SqlErrors.IMPLIED_TAUTOLOGICAL_OR_INCONSISTENT_EXPRESSION, ('redundant_disjunct', Ci.sql())))
                    
                    # (3) each Ai,j redundant?
                    conjuncts = list(Ci.flatten())
                    for j, Aj in enumerate(conjuncts):
                        Aj_z3 = smt.sql_to_z3(Aj, variables)
                        if not smt.is_bool_expr(Aj_z3):
                            continue
                        rest = [smt.sql_to_z3(c, variables) for k, c in enumerate(conjuncts)
                                if k != j and smt.is_bool_expr(smt.sql_to_z3(c, variables))]
                        others = Or(*[smt.sql_to_z3(C, variables) for k, C in enumerate(dnf) if k != i])
                        formula = And(Not(Aj_z3), *rest, Not(others))
                        if not smt.is_satisfiable(formula):
                            results.append(DetectedError(SqlErrors.IMPLIED_TAUTOLOGICAL_OR_INCONSISTENT_EXPRESSION, ('redundant_conjunct', (Ci.sql(), Aj.sql()))))

        return results

    def detect_39_distinct_in_sum_or_avg(self) -> list[DetectedError]:
        '''
            Detect SUM(DISTINCT ...) or AVG(DISTINCT ...)

            If the correct query uses SUM(DISTINCT ...) or AVG(DISTINCT ...), then
            the user query is unlikely to be incorrect, so we do not flag it.
        '''

        results: list[DetectedError] = []

        # Flags for skipping detection if correct query uses DISTINCT in SUM/AVG
        allow_sum_distinct = False
        allow_avg_distinct = False
        
        # First check the correct solutions
        for solution in self.solutions:
            for select in solution.selects:
                ast = select.ast

                if not ast:
                    continue

                for func in ast.find_all(exp.Sum):
                    if func.this and isinstance(func.this, exp.Distinct):
                        allow_sum_distinct = True

                for func in ast.find_all(exp.Avg):
                    if func.this and isinstance(func.this, exp.Distinct):
                        allow_avg_distinct = True

        # Then check the user query
        for select in self.query.selects:
            ast = select.ast

            if not ast:
                continue

            if not allow_sum_distinct:
                # Solution does not use SUM(DISTINCT ...), so check user query
                for func in ast.find_all(exp.Sum):
                    if func.this and isinstance(func.this, exp.Distinct):
                        results.append(DetectedError(SqlErrors.DISTINCT_IN_SUM_OR_AVG, (func.sql(),)))

            if not allow_avg_distinct:
                # Solution does not use AVG(DISTINCT ...), so check user query
                for func in ast.find_all(exp.Avg):
                    if func.this and isinstance(func.this, exp.Distinct):
                        results.append(DetectedError(SqlErrors.DISTINCT_IN_SUM_OR_AVG, (func.sql(),)))

        return results
    
    
    # TODO: implement
    def detect_40_distinct_removing_important_duplicates(self) -> list[DetectedError]:
        return []

    # TODO: refactor
    def detect_41_mixing_comparison_and_null(self) -> list[DetectedError]: 
        '''Detect mixing of >0 with IS NOT NULL or empty string with IS NULL on the same column'''
        return []

        results = []
        # a > 0 AND a IS NOT NULL
        m = re.search(r"(\w+)\s*>\s*0\s+AND\s+\1\s+IS\s+NOT\s+NULL", self.query, re.IGNORECASE)
        if m:
            results.append((
                SqlErrors.SEM_45_MIXING_A_GREATER_THAN_0_WITH_IS_NOT_NULL,
                m.group(0)
            ))

        # a = '' AND a IS NULL
        m2 = re.search(r"(\w+)\s*=\s*''\s+AND\s+\1\s+IS\s+NULL", self.query, re.IGNORECASE)
        if m2:
            results.append((
                SqlErrors.SEM_45_MIXING_A_GREATER_THAN_0_WITH_IS_NOT_NULL,
                m2.group(0)
            ))

        return results    
    
    #TODO: implement
    def detect_42_null_in_InAnyAll_subquery(self) -> list[DetectedError]:
        '''Detect potential NULL/UNKNOWN in IN/ANY/ALL subqueries when subquery column is nullable.
            heuristically assume that if a column is not declared as NOT NULL, then every typical 
            database state contains at least one row in which it is null. '''
        return []

    # TODO: implement
    def detect_43_join_condition_on_unmatchable_column(self) -> list[DetectedError]:
        '''
        For each JOIN … ON: require at least one “A.col = B.col” in the ON clause.
        For comma-style joins (FROM A, B): require at least one “A.col = B.col” in the WHERE.
        If no such predicate is found for a given join, emit SEM_2_JOIN_ON_INCORRECT_COLUMN.
        If the join operation is a self-join, then skip the check.
        Check based on the content of the catalog column_metadata the compatibility of the columns.
        '''
        return []
    
    # TODO: implement
    def detect_44_many_duplicates(self) -> list[DetectedError]:
        return []
    
    # TODO: refactor
    def detect_45_constant_column_output(self) -> list[DetectedError]:
        '''
        Detect when a SELECT-list column is constrained to a constant.
        - If WHERE has A = c and A is in SELECT, warn.
        - If WHERE has A = c and also A = B, then both A and B in SELECT should warn.
        '''
        return []

        results = []

        # 1. Extract selected columns (simple ones only)
        select_cols = set()
        for expr in self.query_map.get("select_value", []):
            expr = expr.strip()
            if expr == "*" or "(" in expr:
                continue
            # Remove potential table qualification and aliases for the check
            col = expr.split("AS")[0].strip().split(".")[-1]
            select_cols.add(col.lower())

        # 2. Extract WHERE clause from the query text
        where_clause_match = re.search(
            r"\bWHERE\b\s+(?P<w>.+?)(?=(?:\bGROUP\b|\bHAVING\b|\bORDER\b|$))",
            self.query, re.IGNORECASE | re.DOTALL
        )
        if not where_clause_match:
            return results

        where_clause = where_clause_match.group("w")

        # Remove subqueries from the WHERE clause text to avoid checking their conditions.
        # This prevents the recognizer from applying a subquery's constraints to the outer query.
        where_clause_no_subs = re.sub(r'\(\s*SELECT.*?\)', '', where_clause, flags=re.IGNORECASE | re.DOTALL)

        # 3. Detect constant columns and column-to-column equalities in the processed clause
        const_re = re.compile(
            r"(?P<col>[a-zA-Z_]\w*(?:\.\w+)?)\s*=\s*(?P<const>'[^']*'|\d+(?:\.\d+)?)",
            re.IGNORECASE
        )
        eq_re = re.compile(
            r"(?P<c1>[a-zA-Z_]\w*(?:\.\w+)?)\s*=\s*(?P<c2>[a-zA-Z_]\w*(?:\.\w+)?)",
            re.IGNORECASE
        )

        const_map = {}
        for m in const_re.finditer(where_clause_no_subs):
            col = m.group("col").split(".")[-1].lower()
            const_map[col] = m.group("const")

        adj = {}
        for m in eq_re.finditer(where_clause_no_subs):
            c1 = m.group("c1").split(".")[-1].lower()
            c2 = m.group("c2").split(".")[-1].lower()
            if c1 in const_map or c2 in const_map:
                continue
            # Avoid self-loops from simple equality checks
            if c1 != c2:
                adj.setdefault(c1, set()).add(c2)
                adj.setdefault(c2, set()).add(c1)

        # 4. Propagate constant constraints via BFS
        constant_cols = set(const_map.keys())
        for start_node in list(const_map):
            queue = [start_node]
            visited = {start_node}
            while queue:
                u = queue.pop(0)
                for v in adj.get(u, []):
                    if v not in visited:
                        visited.add(v)
                        queue.append(v)
            constant_cols.update(visited)

        # 5. Check if any selected columns are constrained to be constant
        for col in select_cols:
            if col in constant_cols:
                # Find the original casing for the error message
                original_col_name = next((c for c in self.query_map.get("select_value", []) if c.lower().endswith(col)), col)
                msg = f"Column `{original_col_name}` in SELECT is constrained to constant"
                results.append((SqlErrors.SEM_50_CONSTANT_COLUMN_OUTPUT, msg))

        return results
    
    # TODO: refactor
    def detect_46_duplicate_column_output(self) -> list[DetectedError]:
        '''
        Detects if the same column or expression appears multiple times in the SELECT list.
        '''
        return []

        results = []

        # 1. Usa il SELECT list già parsato dalla query_map
        select_items = self.query_map.get("select_value", [])
        if not select_items:
            return results

        norm_counts = {}

        for expr in select_items:
            # Normalizza l’espressione: rimuove alias, spazi, case-insensitive
            clean_expr = expr.strip()

            # Rimuovi alias "AS xyz" o finali (non rompere funzioni con parentesi)
            clean_expr = re.sub(r"\s+AS\s+\w+$", "", clean_expr, flags=re.IGNORECASE)
            clean_expr = re.sub(r"\s+\w+$", "", clean_expr)

            # Normalizza spazi e case
            key = clean_expr.strip().lower()
            norm_counts[key] = norm_counts.get(key, 0) + 1

        # 2. Rileva duplicati
        for expr, count in norm_counts.items():
            if count > 1:
                msg = f"Output expression `{expr}` appears {count} times in SELECT"
                results.append((
                    SqlErrors.SEM_51_DUPLICATE_COLUMN_OUTPUT,
                    msg
                ))

        return results



