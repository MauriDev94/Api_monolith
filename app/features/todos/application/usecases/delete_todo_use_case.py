from app.common.use_case import UseCase
from app.core.exceptions.exceptions import NotFoundError
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.application.dto.delete_todo_params import DeleteTodoParams


class DeleteTodo(UseCase[DeleteTodoParams, None]):
    """Delete a todo ensuring ownership by authenticated user."""

    def __init__(self, todo_datasource: TodoDatasource):
        self.todo_datasource = todo_datasource

    def execute(self, params: DeleteTodoParams) -> None:
        existing_todo = self.todo_datasource.get_todo_by_id(params.todo_id)
        if existing_todo is None or existing_todo.user_id != params.user_id:
            raise NotFoundError("todo not found")

        self.todo_datasource.delete_todo(params.todo_id)
        return None
