from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ResourceNotFoundException
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.application.dto.get_todo_by_id_params import GetTodoByIdParams
from app.features.todos.domain.entities.todo import Todo


class GetTodoById(UseCase[GetTodoByIdParams, Todo]):
    """Retrieve a todo by id ensuring ownership by authenticated user."""

    def __init__(self, todo_datasource: TodoDatasource):
        self.todo_datasource = todo_datasource

    def execute(self, params: GetTodoByIdParams) -> Todo:
        todo = self.todo_datasource.get_todo_by_id(params.todo_id)
        if todo is None or todo.user_id != params.user_id:
            raise ResourceNotFoundException("todo not found")
        return todo
