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


def map_todo_entity_to_model(todo_model: TodoModel, todo: Todo) -> TodoModel:
    """Apply mutable domain todo state into an existing ORM todo model."""
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.is_completed = todo.is_completed
    return todo_model
