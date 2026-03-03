from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ResourceNotFoundException
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.application.dto.update_todo_params import UpdateTodoParams
from app.features.todos.domain.entities.todo import Todo


class UpdateTodo(UseCase[UpdateTodoParams, Todo]):
    """Update a todo ensuring ownership by authenticated user."""

    def __init__(self, todo_datasource: TodoDatasource):
        self.todo_datasource = todo_datasource

    def execute(self, params: UpdateTodoParams) -> Todo:
        existing_todo = self.todo_datasource.get_todo_by_id(params.todo_id)
        if existing_todo is None or existing_todo.user_id != params.user_id:
            raise ResourceNotFoundException("todo not found")

        return self.todo_datasource.update_todo(params)
