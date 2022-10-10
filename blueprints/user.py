from datetime import datetime
from flask import (
    Blueprint, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    jsonify, 
    session, 
    flash)
from exts import mail, db
from flask_mail import Message
from models import EmailCaptchaModel, UserModel
import string
import random
from .forms import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:
        form = LoginForm(request.form)
        if form.validate():
            email = form.email.data
            password = form.password.data
            user = UserModel.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect("/")
            else:
                flash("邮箱和密码不匹配！")
                return redirect(url_for("user.login"))
        else:
            flash("邮箱或密码格式错误！")
            return redirect(url_for("user.login"))
            



@bp.route("/register", methods=['POST', 'GET'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'GET':
        return render_template("register.html")
    else:
        if form.validate():
            email = form.email.data
            username = form.username.data
            password = form.password.data
            hash_password = generate_password_hash(password)
            user = UserModel(email=email, username=username, password=hash_password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('user.login'))
        else:
            return redirect(url_for('user.register'))


@bp.route("/logout")
def logout():
    # 清除session中的所有数据
    session.clear()
    return redirect(url_for('user.login'))

# mencached/redis/数据库中

@bp.route("/captcha",methods=['POST'])
def get_captcha():
    # GET,POST
    email = request.form.get("email")
    letters = string.ascii_letters + string.digits
    captcha = "".join(random.sample(letters,4))
    if email:
        message = Message(
            subject="邮箱测试",
            recipients=[email],
            body=f"【Egg问答】您的注册验证码是：{captcha}，请保密并确认本人操作！"
        )
            
        mail.send(message)

        captcha_model = EmailCaptchaModel.query.filter_by(email=email).first()
        if captcha_model:
            captcha_model.captcha = captcha
            captcha_model.create_time = datetime.now()
            db.session.commit()
        else:
            captcha_model = EmailCaptchaModel(email=email,captcha=captcha)
            db.session.add(captcha_model)
            db.session.commit()
        print("captcha:",captcha)
        return jsonify({"code": 200})
        
    else:
        # code: 400,客户端错误
        return jsonify({"code": 400,"message": "请先传递邮箱！"})
