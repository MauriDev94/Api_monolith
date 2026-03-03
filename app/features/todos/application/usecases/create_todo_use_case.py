from app.common.use_case import UseCase
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.application.dto.create_todo_params import CreateTodoParams
from app.features.todos.domain.entities.todo import Todo


class CreateTodo(UseCase[CreateTodoParams, Todo]):
    """Create a new todo item for an authenticated user."""

    def __init__(self, todo_datasource: TodoDatasource):
        self.todo_datasource = todo_datasource

    def execute(self, params: CreateTodoParams) -> Todo:
        return self.todo_datasource.create_todo(params)
