from app.common.use_case import UseCase
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.application.dto.get_todos_params import GetTodosParams
from app.features.todos.domain.entities.todo import Todo


class GetTodos(UseCase[GetTodosParams, list[Todo]]):
    """List todos for an authenticated user."""

    def __init__(self, todo_datasource: TodoDatasource):
        self.todo_datasource = todo_datasource

    def execute(self, params: GetTodosParams) -> list[Todo]:
        return self.todo_datasource.get_todos_by_user_id(params.user_id)
