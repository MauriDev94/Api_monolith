from app.features.todos.application.dto.update_todo_params import UpdateTodoParams
from app.features.todos.domain.entities.todo import Todo
from app.features.todos.infrastructure.models.todo_model import TodoModel


def map_todo_model_to_entity(todo_model: TodoModel) -> Todo:
    """Map ORM todo model to domain entity."""
    return Todo(
        id=todo_model.id,
        user_id=todo_model.user_id,
        title=todo_model.title,
        description=todo_model.description,
        is_completed=todo_model.is_completed,
        created_at=todo_model.created_at,
        updated_at=todo_model.updated_at,
    )


def map_update_todo_params_to_model(todo_model: TodoModel, params: UpdateTodoParams) -> TodoModel:
    """Apply update DTO values into an existing ORM todo model."""
    todo_model.title = params.title
    todo_model.description = params.description
    todo_model.is_completed = params.is_completed
    return todo_model
