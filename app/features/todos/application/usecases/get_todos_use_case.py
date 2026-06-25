from app.common.use_case import UseCase
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.application.dto.get_todos_params import GetTodosParams
from app.features.todos.application.dto.get_todos_result import GetTodosResult


class GetTodos(UseCase[GetTodosParams, GetTodosResult]):
    """List todos for an authenticated user with pagination."""

    def __init__(self, todo_datasource: TodoDatasource):
        self.todo_datasource = todo_datasource

    def execute(self, params: GetTodosParams) -> GetTodosResult:
        todos = self.todo_datasource.get_todos_by_user_id(
            params.user_id, params.limit, params.offset
        )
        total = self.todo_datasource.count_todos_by_user_id(params.user_id)
        return GetTodosResult(
            todos=todos,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )
