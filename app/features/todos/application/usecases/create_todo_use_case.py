from app.common.use_case import UseCase
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.application.dto.create_todo_params import CreateTodoParams
from app.features.todos.domain.entities.todo import Todo


class CreateTodo(UseCase[CreateTodoParams, Todo]):
    """Create a new todo item for an authenticated user."""

    def __init__(self, todo_datasource: TodoDatasource):
        self.todo_datasource = todo_datasource

    def execute(self, params: CreateTodoParams) -> Todo:
        todo = Todo.create_new(
            user_id=params.user_id,
            title=params.title,
            description=params.description,
            due_date=params.due_date,
        )
        return self.todo_datasource.create_todo(todo)
