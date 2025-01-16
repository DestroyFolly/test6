from fastapi import FastAPI, HTTPException
import smtplib
from email.mime.text import MIMEText
from random import randint
import uvicorn
from Models import *
import os

app = FastAPI()
users_db = {}


def send_verification_email(email: str, code: str):
    sender_email = os.environ["sender_email"]
    sender_password = os.environ["sender_password"]

    msg = MIMEText(f'Ваш код подтверждения: {code}')
    msg['Subject'] = 'Код подтверждения'
    msg['From'] = sender_email
    msg['To'] = email

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())


@app.post("/login")
def login(user: UserLogin):
    db_user = users_db.get(user.email)
    if not db_user or db_user["password"] != user.password or not db_user["is_verified"]:
        raise HTTPException(status_code=400, detail="Неверные учетные данные или email не подтвержден")

    return HTTPException(status_code=200, detail="Вход выполнен успешно!")


@app.post("/delete")
def delete(user: UserLogin):
    db_user = users_db.get(user.email)
    if not db_user or db_user["password"] != user.password:
        raise HTTPException(status_code=400, detail="Неверные учетные данные")

    users_db.pop(user.email)
    return HTTPException(status_code=200, detail="Аккаунт удален!")


@app.post("/register")
def register(user: UserCreate):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email уже подтвержден")

    verification_code = str(randint(100000, 999999)) if user.email != test_email else test_code
    users_db[user.email] = {
        "password": user.password,
        "is_verified": False,
        "verification_code": verification_code
    }

    send_verification_email(user.email, verification_code)
    return HTTPException(status_code=200, detail="Пользователь зарегистрирован. "
                                                 "Проверьте вашу почту для подтверждения кода")


@app.post("/verify")
def verify(user: UserVerify):
    user_db = users_db.get(user.email)
    if not user_db or user_db["verification_code"] != user.code:
        raise HTTPException(status_code=400, detail="Неверный код подтверждения")

    user_db["is_verified"] = True
    return HTTPException(status_code=200, detail="Email подтвержден!")


@app.post("/reset-password/request")
def reset_password_request(request: PasswordResetRequest):
    user = users_db.get(request.email)
    if not user or user["password"] != request.old_password:
        raise HTTPException(status_code=400, detail="Неверные учетные данные")

    verification_code = str(randint(100000, 999999)) if request.email != test_email else test_code
    user["verification_code"] = verification_code
    send_verification_email(request.email, verification_code)
    return HTTPException(status_code=200, detail="Код подтверждения отправлен на почту")


@app.post("/reset-password/confirm")
def reset_password_confirm(request: PasswordResetConfirm):
    user = users_db.get(request.email)
    if not user or user["verification_code"] != request.code:
        raise HTTPException(status_code=400, detail="Неверный код подтверждения")

    user["password"] = request.new_password
    return HTTPException(status_code=200, detail="Пароль успешно изменен!")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="debug")
