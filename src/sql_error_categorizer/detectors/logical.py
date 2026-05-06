'''Detector for logical errors in SQL queries.'''

from dataclasses import dataclass
from typing import Callable
from sql_error_taxonomy import SqlErrors
from sqlglot import exp

from .base import BaseDetector, DetectedError
from sqlscope.query import Query, SetOperation

class LogicalErrorDetector(BaseDetector):
    '''Detector for logical errors in SQL queries.'''
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

        # All logical errors require at least one solution to compare against
        # If no solutions are provided, we cannot perform logical error detection
        if not self.solutions:
            return []

        results: list[DetectedError] = super().run()

        checks = [
            self.detect_39_and_instead_of_or,                                       # TODO: implement
            self.detect_52_or_instead_of_and,                                       # TODO: refactor/implement
            self.detect_53_extraneous_not_operator,                                 # TODO: implement
            self.detect_54_missing_not_operator,                                    # TODO: implement
            self.detect_55_substituted_existance_negation_with_less_more_than,      # TODO: implement
            self.detect_57_incorrect_comparison_operator_or_value,                  # TODO: refactor/implement
            self.detect_58_59_62_table_reference_errors,                            # ok
            self.detect_60_join_condition_on_incorrect_column,                      # ok
            self.detect_61_join_condition_with_incorrect_comparison_operator,       # ok
            self.detect_48_missing_join_condition,                                  # ok
            self.detect_104_condition_on_outer_join,                                # ok
            self.detect_63_improper_nesting_of_expressions,                         # TODO: implement
            self.detect_64_improper_nesting_of_subqueries,                          # TODO: implement
            self.detect_65_extraneous_quotes,                                       # TODO: implement
            self.detect_66_missing_expression,                                      # TODO: implement
            self.detect_68_extraneous_expression,                                   # TODO: implement
            self.detect_67_expression_on_incorrect_column,                          # TODO: implement
            self.detect_69_expression_on_incorrect_clause,                          # TODO: implement
            self.detect_43_wildcards_without_like,                                  # ok
            self.detect_110_111_wrong_invalid_wildcard,                             # ok
            self.detect_70_extraneous_column_in_select,                             # ok
            self.detect_71_missing_column_from_select,                              # ok
            self.detect_72_missing_distinct_from_select,                            # ok
            self.detect_73_missing_as_from_select,                                  # ok
            self.detect_74_missing_column_from_order_by,                            # TODO: refactor/implement
            self.detect_75_incorrect_column_in_order_by,                            # TODO: refactor/implement
            self.detect_77_incorrect_ordering_of_rows,                              # TODO: implement
            self.detect_112_118_missing_extraneous_where_clause,                    # ok
            self.detect_113_119_missing_extraneous_group_by_clause,                 # ok
            self.detect_114_120_missing_extraneous_having_clause,                   # ok
            self.detect_115_121_missing_extraneous_order_by_clause,                 # ok
            self.detect_116_121_123_missing_extraneous_incorrect_limit_clause,      # ok
            self.detect_117_122_missing_extraneous_incorrect_offset_clause,         # ok
            self.detect_80_incorrect_function,                                      # TODO: implement
            self.detect_78_distinct_as_function_parameter_when_not_applicable,      # TODO: implement
            self.detect_79_missing_distinct_from_function_parameter,                # TODO: implement
            self.detect_81_incorrect_column_as_function_parameter,                  # TODO: implement
        ]

        for chk in checks:
            results.extend(chk())

        return results
        
    
    def detect_39_and_instead_of_or(self) -> list[DetectedError]:
        return []

    def detect_52_or_instead_of_and(self) -> list[DetectedError]:
        '''
        Detects if OR is used instead of AND in the WHERE or HAVING clauses
        by comparing the query's AST against the correct solution's AST.
        '''
        return []

        results = []
        clauses_to_check = ['where', 'having']

        for clause_name in clauses_to_check:
            # Safely access the clause (e.g., 'where') from both the proposed (q) and correct (s) solution ASTs.
            q_clause = self.q_ast.get('args', {}).get(clause_name)
            s_clause = self.s_ast.get('args', {}).get(clause_name)

            # If the clause doesn't exist in both queries, skip to the next one.
            if not q_clause or not s_clause:
                continue

            # Extract the top-level operator ('And', 'Or', etc.) from the clause.
            q_operator = q_clause.get('args', {}).get('this', {}).get('class')
            s_operator = s_clause.get('args', {}).get('this', {}).get('class')

            # Check if the proposed query incorrectly uses 'Or' when the correct solution uses 'And'.
            if q_operator == 'Or' and s_operator == 'And':
                results.append((
                    SqlErrors.LOG_52_OR_INSTEAD_OF_AND,
                    f"OR used instead of AND in the {clause_name.upper()} clause"
                ))
                
        return results
    
    def detect_53_extraneous_not_operator(self) -> list[DetectedError]:
        return []
    
    def detect_54_missing_not_operator(self) -> list[DetectedError]:
        return []
    
    def detect_55_substituted_existance_negation_with_less_more_than(self) -> list[DetectedError]:
        return []
    
    def detect_57_incorrect_comparison_operator_or_value(self) -> list[DetectedError]:
        '''
        Flags errors in comparison operators or values in WHERE and HAVING clauses.
        
        This function identifies two types of errors:
        1.  An incorrect comparison operator is used (e.g., '<' instead of '>').
        2.  An incorrect literal value is used in a comparison (e.g., 'Morandi' instead of 'Morando').
        '''
        return []

        results = []

        # 1. Extract all comparison tuples from the proposed and correct queries.
        q_comparisons = []
        s_comparisons = []

        # Extract from WHERE clause
        for ast, comp_list in [(self.q_ast, q_comparisons), (self.s_ast, s_comparisons)]:
            clause_node = ast.get('args', {}).get('where', {}).get('args', {}).get('this')
            if clause_node:
                comp_list.extend(self._get_comparisons(clause_node))
            
            # Extract from HAVING clause
            clause_node = ast.get('args', {}).get('having', {}).get('args', {}).get('this')
            if clause_node:
                comp_list.extend(self._get_comparisons(clause_node))

        # 2. Create a map of the correct comparisons for efficient lookup.
        # The key is the column name, and the value is a (operator, value) tuple.
        s_comp_map = {comp[0]: (comp[1], comp[2]) for comp in s_comparisons}

        # 3. Iterate through the proposed query's comparisons and check for mismatches.
        for q_col, q_op, q_val in q_comparisons:
            # Case-insensitive column lookup
            q_col_lower = q_col.lower()
            s_comp_map_lower = {k.lower(): v for k, v in s_comp_map.items()}
            
            if q_col_lower in s_comp_map_lower:
                s_op, s_val = s_comp_map_lower[q_col_lower]

                # Check for an incorrect comparison operator
                if q_op != s_op:
                    results.append((
                        SqlErrors.LOG_57_INCORRECT_COMPARISON_OPERATOR_OR_VALUE,
                        f"Incorrect operator on column '{q_col}'. Found {q_op} but expected {s_op}."
                    ))

                # Check for an incorrect comparison value (exact comparison for all value types)
                if q_val != s_val:
                    results.append((
                        SqlErrors.LOG_57_INCORRECT_COMPARISON_OPERATOR_OR_VALUE,
                        f"Incorrect value in comparison for column '{q_col}'. Found '{q_val}' but expected '{s_val}'."
                    ))
        return results
    
    def detect_58_59_62_table_reference_errors(self) -> list[DetectedError]:
        '''
            Detects join-related errors by comparing the tables used in the proposed query
            against those in the correct solutions.

            This function identifies three types of join errors:
            1. Missing Join: A required table is not included in the proposed query.
            2. Extraneous Join: An unnecessary table is included in the proposed query.
            3. Incorrect Join: A table is included, but it is not the correct one needed for the join.
        '''
                
        @dataclass(frozen=True)
        class TableCol:
            table: str
            column: str

        results: list[DetectedError] = []

        expected_tables: list[set[TableCol]] = []
        actual_tables: set[TableCol] = set()

        # Compute expected tables from solutions
        # NOTE: We expect each solution to use the same set of tables, but we compute
        #       them separately to handle any discrepancies.
        for solution in self.solutions:
            solution_tables: set[TableCol] = set()

            for select in solution.selects:
                for table in select.referenced_tables:
                    if table.cte_idx is not None:
                        continue
                    solution_tables.add(TableCol(table.schema_name, table.real_name))

            expected_tables.append(solution_tables)

        # Compute actual tables from the proposed query
        for select in self.query.selects:
            for table in select.referenced_tables:
                if table.cte_idx is not None:
                    continue
                actual_tables.add(TableCol(table.schema_name, table.real_name))

        # Check for missing joins (expected tables not in actual)
        common_expected_tables = expected_tables[0].intersection(*expected_tables[1:])
        all_expected_tables = expected_tables[0].union(*expected_tables[1:])

        if len(actual_tables) < len(common_expected_tables):
            for missing_table in common_expected_tables - actual_tables:
                results.append(DetectedError(SqlErrors.MISSING_TABLE_REFERENCE, (missing_table.table, missing_table.column)))
        elif len(actual_tables) > len(all_expected_tables):
            for extra_table in actual_tables - all_expected_tables:
                results.append(DetectedError(SqlErrors.EXTRANEOUS_TABLE_REFERENCE, (extra_table.table, extra_table.column)))
        else:
            for wrong_table in actual_tables - all_expected_tables:
                results.append(DetectedError(SqlErrors.INCORRECT_TABLE_REFERENCE, (wrong_table.table, wrong_table.column)))

        return results

    def detect_60_join_condition_on_incorrect_column(self) -> list[DetectedError]:
        return []
    
    def detect_61_join_condition_with_incorrect_comparison_operator(self) -> list[DetectedError]:
        return []
    
    def detect_48_missing_join_condition(self) -> list[DetectedError]:
        return []
    
    def detect_104_condition_on_outer_join(self) -> list[DetectedError]:
        return []

    def detect_63_improper_nesting_of_expressions(self) -> list[DetectedError]:
        return []
    
    def detect_64_improper_nesting_of_subqueries(self) -> list[DetectedError]:
        return []
    
    def detect_65_extraneous_quotes(self) -> list[DetectedError]:
        return []

    def detect_66_missing_expression(self) -> list[DetectedError]:
        return []

    def detect_68_extraneous_expression(self) -> list[DetectedError]:
        return []
    
    def detect_67_expression_on_incorrect_column(self) -> list[DetectedError]:
        return []

    def detect_69_expression_on_incorrect_clause(self) -> list[DetectedError]:
        return []

    def detect_43_wildcards_without_like(self) -> list[DetectedError]:
        '''
            Detect = '%...%' instead of LIKE

            If the correct query uses equality checks containing wildcards characters ('%' or '_'),
            the user query is unlikely to be incorrect, so we do not flag it.
        '''

        results: list[DetectedError] = []

        # First check the correct solutions
        allow_underscore = False
        allow_percent = False

        for solution in self.solutions:
            for select in solution.selects:
                ast = select.ast

                if not ast:
                    continue

                for eq in ast.find_all(exp.EQ):
                    left = eq.this
                    right = eq.expression

                    if isinstance(left, exp.Literal):
                        if has_character(left, '_'):
                            allow_underscore = True
                        if has_character(left, '%'):
                            allow_percent = True

                    if isinstance(right, exp.Literal):
                        if has_character(right, '_'):
                            allow_underscore = True
                        if has_character(right, '%'):
                            allow_percent = True

        for select in self.query.selects:
            ast = select.ast

            if not ast:
                continue

            for eq in ast.find_all(exp.EQ):
                left = eq.this
                right = eq.expression

                if isinstance(left, exp.Literal):
                    if not allow_underscore and has_character(left, '_'):
                        results.append(DetectedError(SqlErrors.WILDCARDS_WITHOUT_LIKE, (str(eq),)))
                        continue
                    if not allow_percent and has_character(left, '%'):
                        results.append(DetectedError(SqlErrors.WILDCARDS_WITHOUT_LIKE, (str(eq),)))
                        continue

                if isinstance(right, exp.Literal):
                    if not allow_underscore and has_character(right, '_'):
                        results.append(DetectedError(SqlErrors.WILDCARDS_WITHOUT_LIKE, (str(eq),)))
                        continue
                    if not allow_percent and has_character(right, '%'):
                        results.append(DetectedError(SqlErrors.WILDCARDS_WITHOUT_LIKE, (str(eq),)))
                        continue

        return results

    def detect_110_111_wrong_invalid_wildcard(self) -> list[DetectedError]:
        '''
            Detect misuse of wildcards, namely:
            - '*' and '?'
            - '_' instead of '%'
            - '%' instead of '_'

            If the correct solution uses the same character,
            the user query is unlikely to be incorrect, so we do not flag it.
        '''

        results: list[DetectedError] = []

        # First check the correct solutions
        underscore_in_solution = False
        percent_in_solution = False
        star_in_solution = False
        question_mark_in_solution = False

        for solution in self.solutions:
            for select in solution.selects:
                ast = select.ast

                if not ast:
                    continue

                for like in ast.find_all(exp.Like):
                    pattern = like.expression
                    if isinstance(pattern, exp.Literal):
                        if has_character(pattern, '_'):
                            underscore_in_solution = True
                        if has_character(pattern, '%'):
                            percent_in_solution = True
                        if has_character(pattern, '*'):
                            star_in_solution = True
                        if has_character(pattern, '?'):
                            question_mark_in_solution = True

        # Then check the user query
        for select in self.query.selects:
            ast = select.ast

            if not ast:
                continue

            for like in ast.find_all(exp.Like):
                pattern = like.expression
                if isinstance(pattern, exp.Literal):
                    # query contains '*' while solution does not
                    # most likely an attempt to use '%' wildcard
                    if not star_in_solution and has_character(pattern, '*'):
                        results.append(DetectedError(SqlErrors.INVALID_WILDCARD, (str(like),)))

                    # query contains '?' while solution does not
                    # most likely an attempt to use '_' wildcard
                    if not question_mark_in_solution and has_character(pattern, '?'):
                        results.append(DetectedError(SqlErrors.INVALID_WILDCARD, (str(like),)))

                    # '_' instead of '%'
                    if percent_in_solution and not underscore_in_solution:
                        if has_character(pattern, '_') and not has_character(pattern, '%'):
                            results.append(DetectedError(SqlErrors.WRONG_WILDCARD, (str(like),)))

                    # '%' instead of '_'
                    if underscore_in_solution and not percent_in_solution:
                        if has_character(pattern, '%') and not has_character(pattern, '_'):
                            results.append(DetectedError(SqlErrors.WRONG_WILDCARD, (str(like),)))


        
        return results

    def detect_70_extraneous_column_in_select(self) -> list[DetectedError]:
        '''
        Flags when an extraneous column is included in the SELECT clause.
        '''

        results: list[DetectedError] = []

        # First, check if the number of columns exceeds the maximum required by any solution
        column_number_required_max = max(len(sol.main_query.output.columns) for sol in self.solutions)
        column_number_provided = len(self.query.main_query.output.columns)

        if column_number_provided > column_number_required_max:
            results.append(DetectedError(SqlErrors.EXTRANEOUS_COLUMN_IN_SELECT, (column_number_provided, column_number_required_max)))

        # Then, check for specific extraneous columns
        columns_required = set.union(*[sol.output_columns_source for sol in self.solutions])
        columns_provided = self.query.output_columns_source
        extraneous_columns = columns_provided - columns_required

        for schema, table, column in extraneous_columns:
            results.append(DetectedError(SqlErrors.EXTRANEOUS_COLUMN_IN_SELECT, (schema, table, column)))

        return results
    
    def detect_71_missing_column_from_select(self) -> list[DetectedError]:
        '''
        Flags when a required column is missing from the SELECT clause.
        '''

        results: list[DetectedError] = []

        # First, check if the number of columns is less than the minimum required by any solution
        column_number_required_min = min(len(sol.main_query.output.columns) for sol in self.solutions)
        column_number_provided = len(self.query.main_query.output.columns)

        if column_number_provided < column_number_required_min:
            results.append(DetectedError(SqlErrors.MISSING_COLUMN_FROM_SELECT, (column_number_provided, column_number_required_min)))

        # Then, check for specific missing columns
        columns_required = set.union(*[sol.output_columns_source for sol in self.solutions])
        columns_provided = self.query.output_columns_source
        missing_columns = columns_required - columns_provided

        for schema, table, column in missing_columns:
            results.append(DetectedError(SqlErrors.MISSING_COLUMN_FROM_SELECT, (schema, table, column)))

        return results
    
    def detect_72_missing_distinct_from_select(self) -> list[DetectedError]:
        '''Flags when DISTINCT is missing from a SELECT that requires it.'''

        def _is_distinct(so: SetOperation) -> bool:
            output = so.output
            columns = len(output.columns)
            longest_constraint = max(len(c.columns) for c in output.unique_constraints) if output.unique_constraints else 0

            return longest_constraint >= columns

        # ensure all solutions are DISTINCT
        requires_distinct = all(_is_distinct(sol.main_query) for sol in self.solutions)

        # At least one solution doesn't require DISTINCT, so it's not necessary for the query
        # Skip this check
        if not requires_distinct:
            return []
        
        if not _is_distinct(self.query.main_query):
            return [DetectedError(SqlErrors.MISSING_DISTINCT_FROM_SELECT)]
        
        return []

    def detect_73_missing_as_from_select(self) -> list[DetectedError]:
        '''
            Flags when AS aliases are missing from required columns in the SELECT clause.
        '''
        
        results: list[DetectedError] = []

        # ensure we have the correct columns in both amount and source
        extraneous_columns = self.detect_70_extraneous_column_in_select()
        missing_columns = self.detect_71_missing_column_from_select()

        if extraneous_columns or missing_columns:
            return results  # skip AS check if column count is already wrong

        # only consider columns that are actually aliased
        expected_aliases: set[str] = set.intersection(*[set(col.name for col in sol.main_query.output.columns if col.name != col.real_name and not col.name.startswith('_')) for sol in self.solutions])
        provided_aliases: set[str] = set(col.name for col in self.query.main_query.output.columns if col.name != col.real_name and not col.name.startswith('_'))

        missing_aliases = expected_aliases - provided_aliases

        for alias in missing_aliases:
            results.append(DetectedError(SqlErrors.MISSING_AS_FROM_SELECT, (alias,)))

        return results

    def detect_74_missing_column_from_order_by(self) -> list[DetectedError]:
        '''Flags when a required column is missing from the ORDER BY clause.'''
        results: list[DetectedError] = []

        # for select in self.query.main_query.main_selects:
        #     if not select.order_by:
        #         continue

        #     order_by_cols: list[] = []

        #     # 1. Extract columns from the query's ORDER BY clause and map them to referenced tables

        return results
    
        results = []
        if not self.q_ast or not self.s_ast:
            return results

        q_orderby_cols = self._get_orderby_columns(self.q_ast)
        s_orderby_cols = self._get_orderby_columns(self.s_ast)

        # Create sets of column names for easy comparison (case-insensitive)
        q_cols_set = {col.lower() for col, direction in q_orderby_cols}
        s_cols_set = {col.lower() for col, direction in s_orderby_cols}
        
        # Find columns in the solution's ORDER BY that are not in the user's
        missing_cols = s_cols_set - q_cols_set
        for col_lower in missing_cols:
            # Find the original case from the solution
            original_col = next((col for col, direction in s_orderby_cols if col.lower() == col_lower), col_lower)
            results.append((
                SqlErrors.LOG_74_MISSING_COLUMN_FROM_ORDER_BY,
                f"The column '{original_col}' is missing from the ORDER BY clause."
            ))
        return results

    def detect_75_incorrect_column_in_order_by(self) -> list[DetectedError]:
        '''Flags when a column is incorrectly included in the ORDER BY clause.'''
        return []
    
        results = []
        if not self.q_ast or not self.s_ast:
            return results

        q_orderby_cols = self._get_orderby_columns(self.q_ast)
        s_orderby_cols = self._get_orderby_columns(self.s_ast)

        # Create sets of column names for easy comparison (case-insensitive)
        q_cols_set = {col.lower() for col, direction in q_orderby_cols}
        s_cols_set = {col.lower() for col, direction in s_orderby_cols}
        
        # Find columns in the user's ORDER BY that are not in the solution's
        incorrect_cols = q_cols_set - s_cols_set
        for col_lower in incorrect_cols:
            # Find the original case from the query
            original_col = next((col for col, direction in q_orderby_cols if col.lower() == col_lower), col_lower)
            results.append((
                SqlErrors.LOG_75_INCORRECT_COLUMN_IN_ORDER_BY,
                f"The column '{original_col}' should not be in the ORDER BY clause."
            ))
        return results

    def detect_77_incorrect_ordering_of_rows(self) -> list[DetectedError]:
        return []
    
    def detect_112_118_missing_extraneous_where_clause(self) -> list[DetectedError]:
        results: list[DetectedError] = []

        # If all solutions have a WHERE clause, then the user's query should have one as well
        # If all solutions don't have a WHERE clause, then the user's query shouldn't have one either
        # Otherwise, we cannot be sure if a WHERE clause is required or not, so we skip this check to avoid false positives
        solution_has_where: set[bool] = set()
        for solution in self.solutions:
            solution_has_where.add(any(select.where for select in solution.selects))

        user_has_where = any(select.where for select in self.query.selects)

        if solution_has_where == {True} and not user_has_where:
            results.append(DetectedError(SqlErrors.MISSING_WHERE_CLAUSE))
        elif solution_has_where == {False} and user_has_where:
            results.append(DetectedError(SqlErrors.EXTRANEOUS_WHERE_CLAUSE))

        return results
    
    def detect_113_119_missing_extraneous_group_by_clause(self) -> list[DetectedError]:
        results: list[DetectedError] = []

        # If all solutions have a GROUP BY clause, then the user's query should have one as well
        # If all solutions don't have a GROUP BY clause, then the user's query shouldn't have one either
        # Otherwise, we cannot be sure if a GROUP BY clause is required or not, so we skip this check to avoid false positives
        solution_has_group_by: set[bool] = set()
        for solution in self.solutions:
            solution_has_group_by.add(any(select.group_by for select in solution.selects))

        user_has_group_by = any(select.group_by for select in self.query.selects)

        if solution_has_group_by == {True} and not user_has_group_by:
            results.append(DetectedError(SqlErrors.MISSING_GROUP_BY_CLAUSE))
        elif solution_has_group_by == {False} and user_has_group_by:
            results.append(DetectedError(SqlErrors.EXTRANEOUS_GROUP_BY_CLAUSE))
    
        return results
    
    def detect_114_120_missing_extraneous_having_clause(self) -> list[DetectedError]:
        results: list[DetectedError] = []

        # If all solutions have a HAVING clause, then the user's query should have one as well
        # If all solutions don't have a HAVING clause, then the user's query shouldn't have one either
        # Otherwise, we cannot be sure if a HAVING clause is required or not, so we skip this check to avoid false positives
        solution_has_having: set[bool] = set()
        for solution in self.solutions:
            solution_has_having.add(any(select.having for select in solution.selects))

        user_has_having = any(select.having for select in self.query.selects)

        if solution_has_having == {True} and not user_has_having:
            results.append(DetectedError(SqlErrors.MISSING_HAVING_CLAUSE))
        elif solution_has_having == {False} and user_has_having:
            results.append(DetectedError(SqlErrors.EXTRANEOUS_HAVING_CLAUSE))

        return results

    def detect_115_121_missing_extraneous_order_by_clause(self) -> list[DetectedError]:
        results: list[DetectedError] = []

        # If all solutions have an ORDER BY clause, then the user's query should have one as well
        # If all solutions don't have an ORDER BY clause, then the user's query shouldn't have one either
        # Otherwise, we cannot be sure if an ORDER BY clause is required or not, so we skip this check to avoid false positives
        solution_has_order_by: set[bool] = set()
        for solution in self.solutions:
            solution_has_order_by.add(any(select.order_by for select in solution.selects))

        user_has_order_by = any(select.order_by for select in self.query.selects)

        if solution_has_order_by == {True} and not user_has_order_by:
            results.append(DetectedError(SqlErrors.MISSING_ORDER_BY_CLAUSE))
        elif solution_has_order_by == {False} and user_has_order_by:
            results.append(DetectedError(SqlErrors.EXTRANEOUS_ORDER_BY_CLAUSE))

        return results

    def detect_116_121_123_missing_extraneous_incorrect_limit_clause(self) -> list[DetectedError]:
        results: list[DetectedError] = []

        # Save all possible limit values from solutions to handle cases where multiple solutions have different limits,
        #  as well as set operations, which would be too complex to map to their limit values directly
        solution_limits: set[int | None] = set()
        
        # If all solutions have a LIMIT clause, then the user's query should have one as well
        for solution in self.solutions:
            # Only check main selects for LIMIT clause, since LIMIT on subqueries is less common and often not required
            for select in solution.main_query.main_selects:
                solution_limits.add(select.limit)

        user_limits: set[int] = set()
        for select in self.query.main_query.main_selects:
            if select.limit is not None:
                user_limits.add(select.limit)

        # if at least a solution doesn't have a limit, but other solutions do, we cannot be sure if a limit is required or not, so we skip this check to avoid false positives
        if None in solution_limits and len(solution_limits) > 1:
            return results
        
        solution_limits.discard(None)  # remove None if present, since we already handled the case where some solutions have limits and others don't

        if solution_limits and not user_limits:
            results.append(DetectedError(SqlErrors.MISSING_LIMIT_CLAUSE))
        elif not solution_limits and user_limits:
            results.append(DetectedError(SqlErrors.EXTRANEOUS_LIMIT_CLAUSE))
        elif solution_limits and user_limits and not user_limits.issubset(solution_limits):
            results.append(DetectedError(SqlErrors.INCORRECT_LIMIT, (user_limits, solution_limits)))

        return results

    def detect_117_122_missing_extraneous_incorrect_offset_clause(self) -> list[DetectedError]:
        results: list[DetectedError] = []

        # Save all possible offset values from solutions to handle cases where multiple solutions have different offsets,
        #  as well as set operations, which would be too complex to map to their offset values directly
        solution_offsets: set[int | None] = set()
        for solution in self.solutions:
            # Only check main selects for OFFSET clause, since OFFSET on subqueries is less common and often not required
            for select in solution.main_query.main_selects:
                solution_offsets.add(select.offset)

        user_offsets: set[int] = set()
        for select in self.query.main_query.main_selects:
            if select.offset is not None:
                user_offsets.add(select.offset)

        # if at least a solution doesn't have an offset, but other solutions do, we cannot be sure if an offset is required or not, so we skip this check to avoid false positives
        if None in solution_offsets and len(solution_offsets) > 1:
            return results
        
        solution_offsets.discard(None)  # remove None if present, since we already handled the case where some solutions have offsets and others don't

        if solution_offsets and not user_offsets:
            results.append(DetectedError(SqlErrors.MISSING_OFFSET_CLAUSE))
        elif not solution_offsets and user_offsets:
            results.append(DetectedError(SqlErrors.EXTRANEOUS_OFFSET_CLAUSE))
        elif solution_offsets and user_offsets and not user_offsets.issubset(solution_offsets):
            results.append(DetectedError(SqlErrors.INCORRECT_OFFSET, (user_offsets, solution_offsets)))

        return results

    def detect_80_incorrect_function(self) -> list[DetectedError]:
        return []

    def detect_78_distinct_as_function_parameter_when_not_applicable(self) -> list[DetectedError]:
        return []

    def detect_79_missing_distinct_from_function_parameter(self) -> list[DetectedError]:
        return []
    
    def detect_81_incorrect_column_as_function_parameter(self) -> list[DetectedError]:
        return []
    
# region Helper methods
def has_character(literal: exp.Literal, chars: str) -> bool:
    '''
        Check if the literal contains a specific character.
        If `chars` contains multiple characters, check if any of them are present.
    '''
    value = literal.this

    if not isinstance(value, str):
        return False

    return any(c in value for c in chars)
# endregion 
