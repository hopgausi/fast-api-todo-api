from fastapi import FastAPI, Path, Query, HTTPException, Body, status
from typing import Annotated
from enum import Enum
from pydantic import BaseModel, Field

app = FastAPI(
    title='Todo API',
    description='A simple todo API',
    version='0.0.1',
)

class Status(str, Enum):
    pending = 'pending'
    completed = 'completed'
    in_progress = 'in progress'

class User(BaseModel):
    id: int = Field(primary_key=True)
    first_name: str
    last_name: str

class UpdateUser(BaseModel):
    first_name: str | None = None
    last_name: str | None = None

class ToDoItem(BaseModel):
    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key=True)
    title: str
    description: str
    status: Status = Status.pending

class ToDoItemUpdate(BaseModel):
    user_id: int | None = None
    title: str | None = None
    description: str | None = None
    status: Status | None = None

db_users: list[User] = [
    User(
        id=1,
        first_name='John',
        last_name='Doe'
    ),
    User(
        id=2,
        first_name='Jane',
        last_name='Doe'
    ),
]

db_todos: list[ToDoItem] = [
    ToDoItem(
        id=1,
        user_id=2,
        title='Buy groceries',
        description='Buy groceries from the supermarket',
        status=Status.pending
    ),
    ToDoItem(
        id=2,
        user_id=1,
        title='Do laundry',
        description='Do laundry and fold clothes',
        status=Status.pending
    ),
]

def get_todo_list(db_todos: ToDoItem, db_users: User) -> list:
    todos = []
    for todo in db_todos:
        todo = todo.model_dump()
        for user in db_users:
            if todo['user_id'] == user.id:
                todo['user'] = user.model_dump()
        todo.pop('user_id')
        todos.append(todo)
    return todos

def filter_todos_by_status(todos: list, status: str)->list:
    return [todo for todo in todos if todo['status'] == status]


def search_todos(todos: list, q: str) -> list:
    return [todo for todo in todos if q.lower() in todo['title'].lower()]


def check_if_user_exists(user_id: int, db_users: User) -> bool:
    user_exists = False
    for user in db_users:
        if user.id == user_id:
            user_exists = True
            break
    return user_exists


def check_if_todo_already_exists(todo: ToDoItem, db_todos: list[ToDoItem]):
    already_exists = False
    for db_todo in db_todos:
        if db_todo.id == todo.id or db_todo.title.lower() == todo.title.lower():
            already_exists = True
    return already_exists


@app.get('/todos', tags=['todos'])
async def get_todos(
        status: Annotated[
            Status | None, 
            Query(
                description='The status of the todo item to get'
            )
        ] = 'All',
        q: Annotated[
            str | None, 
            Query(
                description='The search query string'
            )
        ] = None
    ):
    todos = get_todo_list(db_todos, db_users)
    if status != 'All':
        todos = filter_todos_by_status(todos, status)
    if q:
        todos = search_todos(todos, q)
    return todos
    

@app.get('/todos/{todo_id}', tags=['todos'])
async def get_todo(
        todo_id: Annotated[int,Path(gt=0, title='The ID of the todo item to get')],
    ):
    for todo in db_todos:
        if todo.id == todo_id:
            todo = todo.model_dump()
            for user in db_users:
                if todo['user_id'] == user.id:
                    todo['user'] = user.model_dump()
            todo.pop('user_id')
            return todo
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Todo not found')


@app.post('/todos', tags=['todos'])
async def create_todo(
        todo: Annotated[ToDoItem, Body(description='The todo item to create')]
    ):
    if not check_if_user_exists(todo.user_id, db_users):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    if check_if_todo_already_exists(todo, db_todos):
        raise HTTPException(status.HTTP_226_IM_USED, detail='A todo with the same title or id already exists')
    db_todos.append(todo)
    return { 'status' : status.HTTP_201_CREATED, 'data' : todo }


@app.put('/todos/{todo_id}', tags=['todos'])
async def update_todo(*,
        todo_id: Annotated[int, Path(gt=0, title='The ID of the todo item to update')],
        todo: Annotated[ToDoItemUpdate, Body(description='The todo item to update')]
    ):
    for db_todo in db_todos:
        if db_todo.id == todo_id:
            if todo.title:
                db_todo.title = todo.title
            if todo.description:
                db_todo.description = todo.description
            if todo.status:
                db_todo.status = todo.status
            if todo.user_id:
                if not check_if_user_exists(todo.user_id, db_users):
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
                db_todo.user_id = todo.user_id
            return { 'status' : status.HTTP_200_OK, 'data' : db_todo }
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Todo not found')


@app.delete('/todos/{todo_id}', tags=['todos'])
async def delete_todo(
        todo_id: Annotated[int, Path(gt=0, title='The ID of the todo item to delete')]
    ):
    for todo in db_todos:
        if todo.id == todo_id:
            db_todos.remove(todo)
            return { 'status' : status.HTTP_200_OK, 'data' : { 'delete' : True } }
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Todo not found')

@app.get('/users', tags=['users'])
async def get_users():
    return db_users

@app.get('/users/{user_id}', tags=['users'])
async def get_user(
        user_id: Annotated[int, Path(gt=0, title='The ID of the user to get')]
    ):
    for user in db_users:
        if user.id == user_id:
            return user
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

@app.post('/users', tags=['users'])
async def create_user(
        user: Annotated[User, Body(description='The user to create')]
    ):
    if check_if_user_exists(user.id, db_users):
        raise HTTPException(status_code=status.HTTP_226_IM_USED, detail='A user with the same id already exists')
    db_users.append(user)
    return { 'status' : status.HTTP_201_CREATED, 'data' : user }

@app.put('/users/{user_id}', tags=['users'])
async def update_user(*,
    user_id: Annotated[int, Path(gt=0, title='The ID of the user to update')],
    user: Annotated[UpdateUser, Body(description='The user to update')]
    ):
    for db_user in db_users:
        if db_user.id == user_id:
            if user.first_name:
                db_user.first_name = user.first_name
            if user.last_name:
                db_user.last_name = user.last_name
            return { 'status' : status.HTTP_200_OK, 'data' : db_user }
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')