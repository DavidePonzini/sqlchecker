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
            self.detect_47_and_instead_of_or,
            self.detect_48_or_instead_of_and,
            self.detect_49_extraneous_not_operator,
            self.detect_50_missing_not_operator,
            self.detect_51_substituted_existance_negation_with_less_more_than,
            self.detect_52_incorrect_comparison_operator_or_value,
            self.detect_53_54_55_table_reference_errors,
            self.detect_56_join_condition_on_incorrect_column,
            self.detect_57_join_condition_with_incorrect_comparison_operator,
            self.detect_58_omitted_join_condition,
            self.detect_59_condition_on_outer_join,
            self.detect_60_improper_nesting_of_expressions,
            self.detect_61_improper_nesting_of_subqueries,
            self.detect_62_extraneous_quotes,
            self.detect_63_missing_expression,
            self.detect_64_extraneous_expression,
            self.detect_65_expression_on_incorrect_column,
            self.detect_66_expression_on_incorrect_clause,
            self.detect_67_wildcards_without_like,
            self.detect_68_69_wrong_invalid_wildcard,
            self.detect_70_extraneous_column_in_select,
            self.detect_71_missing_column_from_select,
            self.detect_72_missing_distinct_from_select,
            self.detect_73_missing_as_from_select,
            self.detect_74_missing_column_from_order_by,
            self.detect_75_incorrect_column_in_order_by,
            self.detect_76_incorrect_ordering_of_rows,
            self.detect_77_missing_where_clause,
            self.detect_78_missing_group_by_clause,
            self.detect_79_missing_having_clause,
            self.detect_80_missing_order_by_clause,
            self.detect_81_missing_limit_clause,
            self.detect_82_missing_offset_clause,
            self.detect_83_extraneous_where_clause,
            self.detect_84_extraneous_group_by_clause,
            self.detect_85_extraneous_having_clause,
            self.detect_86_extraneous_order_by_clause,
            self.detect_87_extraneous_limit_clause,
            self.detect_88_extraneous_offset_clause,
            self.detect_89_incorrect_limit,
            self.detect_90_incorrect_offset,
            self.detect_91_incorrect_function,
            self.detect_92_distinct_as_function_parameter_when_not_applicable,
            self.detect_93_missing_distinct_from_function_parameter,
            self.detect_94_incorrect_column_as_function_parameter,
        ]

        for chk in checks:
            results.extend(chk())

        return results
        
    # TODO: implement
    def detect_47_and_instead_of_or(self) -> list[DetectedError]:
        return []

    # TODO: refactor
    def detect_48_or_instead_of_and(self) -> list[DetectedError]:
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
    
    # TODO: implement
    def detect_49_extraneous_not_operator(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_50_missing_not_operator(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_51_substituted_existance_negation_with_less_more_than(self) -> list[DetectedError]:
        return []
    
    # TODO: refactor
    def detect_52_incorrect_comparison_operator_or_value(self) -> list[DetectedError]:
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
    
    def detect_53_54_55_table_reference_errors(self) -> list[DetectedError]:
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

    
    # TODO: implement
    def detect_56_join_condition_on_incorrect_column(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_57_join_condition_with_incorrect_comparison_operator(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_58_omitted_join_condition(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_59_condition_on_outer_join(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_60_improper_nesting_of_expressions(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_61_improper_nesting_of_subqueries(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_62_extraneous_quotes(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_63_missing_expression(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_64_extraneous_expression(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_65_expression_on_incorrect_column(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_66_expression_on_incorrect_clause(self) -> list[DetectedError]:
        return []

    def detect_67_wildcards_without_like(self) -> list[DetectedError]:
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

    def detect_68_69_wrong_invalid_wildcard(self) -> list[DetectedError]:
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
                    if not self.solutions:
                        # No solutions to compare against
                        # Fall back to detecting just '*' or '?' usage
                        if has_character(pattern, '*') or has_character(pattern, '?'):
                            results.append(DetectedError(SqlErrors.INVALID_WILDCARD, (str(like),)))
                        continue

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


    # TODO: refactor
    def detect_74_missing_column_from_order_by(self) -> list[DetectedError]:
        '''Flags when a required column is missing from the ORDER BY clause.'''
        return []
    
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

    # TODO: refactor
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

    # TODO: implement
    def detect_76_incorrect_ordering_of_rows(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_77_missing_where_clause(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_78_missing_group_by_clause(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_79_missing_having_clause(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_80_missing_order_by_clause(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_81_missing_limit_clause(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_82_missing_offset_clause(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_83_extraneous_where_clause(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_84_extraneous_group_by_clause(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_85_extraneous_having_clause(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_86_extraneous_order_by_clause(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_87_extraneous_limit_clause(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_88_extraneous_offset_clause(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_89_incorrect_limit(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_90_incorrect_offset(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_91_incorrect_function(self) -> list[DetectedError]:
        return []


    # TODO: implement
    def detect_92_distinct_as_function_parameter_when_not_applicable(self) -> list[DetectedError]:
        return []

    # TODO: implement
    def detect_93_missing_distinct_from_function_parameter(self) -> list[DetectedError]:
        return []
    
    # TODO: implement
    def detect_94_incorrect_column_as_function_parameter(self) -> list[DetectedError]:
        return []
    
    #region Utility methods
    def _get_comparisons(self, node: dict) -> list:
        '''
        Recursively traverses an AST node to find all comparison expressions.
        
        Args:
            node: The AST node to start traversal from.
            
        Returns:
            A list of tuples, where each tuple represents a comparison in the
            form (column_name, operator_class, literal_value).
        '''
        if not node or not isinstance(node, dict):
            return []

        node_class = node.get('class')
        args = node.get('args', {})

        # Base case: The node is a comparison operator (e.g., EQ, LT, GT).
        comparison_operators = {'EQ', 'NE', 'GT', 'GTE', 'LT', 'LTE'}
        if node_class in comparison_operators:
            left_operand = args.get('this', {})
            right_operand = args.get('expression', {})

            # We only evaluate simple "Column <operator> Literal" expressions.
            if left_operand.get('class') == 'Column' and right_operand.get('class') == 'Literal':
                try:
                    column_name = left_operand['args']['this']['args']['this']
                    literal_value = right_operand['args']['this']
                    return [(column_name, node_class, literal_value)]
                except KeyError:
                    return [] # AST structure is not as expected.
            return []

        # Recursive step: The node is a logical combiner (AND, OR).
        logical_operators = {'And', 'Or'}
        if node_class in logical_operators:
            left_results = self._get_comparisons(args.get('this'))
            right_results = self._get_comparisons(args.get('expression'))
            return left_results + right_results
        
        return []
    
    def _get_structured_expressions(self, ast: dict) -> list:
        '''
        Extracts a list of structured representations of aggregate/function expressions
        from a SELECT query's AST.

        Args:
            ast: The Abstract Syntax Tree of the query.

        Returns:
            A list of tuples, e.g., [('AVG', 'Age'), ('COUNT', '*')].
        '''
        structured_exprs = []
        if not ast:
            return structured_exprs

        # Navigate to the list of expressions in the SELECT clause
        select_expressions = ast.get('args', {}).get('expressions', [])
        
        for expr_node in select_expressions:
            node_class = expr_node.get('class')
            
            # Check for common aggregate functions
            if node_class in {'Avg', 'Sum', 'Count', 'Min', 'Max'}:
                target_node = expr_node.get('args', {}).get('this', {})
                
                # Handle the case of COUNT(*)
                if target_node.get('class') == 'Star':
                    structured_exprs.append((node_class, '*'))
                # Handle functions on a specific column, e.g., AVG(Age)
                elif target_node.get('class') == 'Column':
                    try:
                        col_name = target_node['args']['this']['args']['this']
                        structured_exprs.append((node_class, col_name))
                    except KeyError:
                        # Could not parse column name, so skip this expression
                        continue
        return structured_exprs
    
    def _get_select_columns(self, ast: dict) -> list:
        '''
        Extracts a list of simple column names from a SELECT query's AST.
        This version handles simple columns, qualified columns (table.col), and aliased columns.
        '''
        columns = []
        if not ast:
            return columns

        select_expressions = ast.get('args', {}).get('expressions', [])
        
        for expr_node in select_expressions:
            # This recursive helper will dive into aliases to find the base column.
            col_name = self._find_underlying_column(expr_node)
            if col_name:
                # Normalize to lowercase for case-insensitive comparison
                columns.append(col_name.lower())
        
        return columns

    def _find_underlying_column(self, node: dict):
        '''
        Recursively traverses an expression node to find the underlying column identifier.
        '''
        if not isinstance(node, dict):
            return None
        
        node_class = node.get('class')

        # Base case: We found a column. Handle both qualified and simple names.
        if node_class == 'Column':
            try:
                # Qualified column name, e.g., c1.cID -> 'cID'
                return node['args']['expression']['args']['this']
            except (KeyError, TypeError):
                try:
                    # Simple column name, e.g., cID -> 'cID'
                    return node['args']['this']['args']['this']
                except (KeyError, TypeError):
                    return None

        # Recursive step: The node is an alias, so check the aliased expression.
        if node_class == 'Alias':
            return self._find_underlying_column(node.get('args', {}).get('this'))
        
        # Return None if it's another type of expression (e.g., a function or literal)
        return None
    
    def _selects_star(self, ast: dict) -> bool:
        '''
        Checks if a `SELECT *` is used in the query by looking for a 'Star'
        node in the AST's expression list.

        Args:
            ast: The Abstract Syntax Tree of the query.

        Returns:
            True if `SELECT *` is found, otherwise False.
        '''
        if not ast:
            return False
        try:
            select_expressions = ast['args']['expressions']
            for expr_node in select_expressions:
                if expr_node.get('class') == 'Star':
                    return True
        except (KeyError, TypeError):
            # Handles cases where the AST structure is unexpected
            return False
        return False
    
    def _get_orderby_columns(self, ast: dict) -> list:
        '''
        Extracts a list of columns and their sort direction from an ORDER BY clause.

        Args:
            ast: The Abstract Syntax Tree of the query.

        Returns:
            A list of tuples, e.g., [('col_name', 'ASC'), ('col_name2', 'DESC')].
        '''
        orderby_terms = []
        if not ast:
            return orderby_terms

        orderby_node = ast.get('args', {}).get('order')
        if not orderby_node:
            return orderby_terms

        try:
            for term_node in orderby_node['args']['expressions']:
                if term_node.get('class') != 'Ordered':
                    continue
                
                column_node = term_node.get('args', {}).get('this')
                
                col_name = self._find_underlying_column(column_node)
                
                if col_name:
                    # Check for the 'desc' boolean flag in the term's arguments.
                    is_desc = term_node.get('args', {}).get('desc', False)
                    direction = 'DESC' if is_desc else 'ASC'
                    orderby_terms.append((col_name, direction))
        except (KeyError, AttributeError):
            return []
            
        return orderby_terms
    #endregion Utility methods

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