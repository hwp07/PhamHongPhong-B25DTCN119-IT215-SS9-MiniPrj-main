from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI()

tickets_db = [
    {"id": 1, "movie_name": "Doctor Strange 3", "room_code": "IMAX-01", "quantity": 2, "status": "confirmed", "created_at": "2026-07-01T19:00:00Z"},
    {"id": 2, "movie_name": "Avatar 3", "room_code": "PREMIUM-02", "quantity": 1, "status": "confirmed", "created_at": "2026-07-01T20:15:00Z"}
]


class Ticket(BaseModel):
    movie_name: str = Field(..., min_length=1)
    room_code: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1, le=10)


def response_json(
    statusCode: int,
    message: str,
    data: Any,
    error: Any,
    path: str,
):
    return JSONResponse(
        status_code=statusCode,
        content={
            "statusCode": statusCode,
            "message": message,
            "data": data,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "path": path,
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return response_json(
        statusCode=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Dữ liệu đầu vào không hợp lệ!",
        data=None,
        error=exc.errors(),
        path=request.url.path,
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    return response_json(
        statusCode=exc.status_code,
        message=exc.detail,
        data=None,
        error=exc.detail,
        path=request.url.path,
    )


@app.exception_handler(Exception)
async def server_exception_handler(
    request: Request,
    exc: Exception,
):
    return response_json(
        statusCode=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Lỗi hệ thống!",
        data=None,
        error=str(exc),
        path=request.url.path,
    )


@app.get("/tickets")
def get_all_tickets(request: Request):
    return response_json(
        statusCode=status.HTTP_200_OK,
        message="Lấy danh sách vé thành công!",
        data=tickets_db,
        error=None,
        path=request.url.path,
    )

@app.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: Ticket, request: Request):
    for item in tickets_db:
        if (
            item["movie_name"].lower() == ticket.movie_name.lower()
            and item["room_code"].lower() == ticket.room_code.lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ERR-CINE-01: Ticket conflict for movie and room combination.",
            )

    new_ticket = {
        "id": len(tickets_db) + 1,
        **ticket.model_dump(),
        "status": "confirmed",
        "created_at": datetime.now().isoformat() + "Z",
    }

    tickets_db.append(new_ticket)

    return response_json(
        statusCode=status.HTTP_201_CREATED,
        message="Đặt vé thành công!",
        data=new_ticket,
        error=None,
        path=request.url.path,
    )

@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_200_OK)
def delete_ticket(ticket_id: int, request: Request):
    ticket = None

    for item in tickets_db:
        if item["id"] == ticket_id:
            ticket = item
            break

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ERR-CINE-02: Ticket ID does not exist.",
        )

    tickets_db.remove(ticket)

    return response_json(
        statusCode=status.HTTP_200_OK,
        message="Hủy vé thành công!",
        data=None,
        error=None,
        path=request.url.path,
    )
