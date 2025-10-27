import os
import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect

# --- モデルとフォームをインポート (変更) ---
from models import db, User, SupportRequest, SOSSignal, ChatMessage, CommunityPost, Group, GroupChatMessage
from forms import (
    LoginForm, RegistrationForm, SupportRequestForm,
    ChatForm, CommunityPostForm, CreateGroupForm, GroupChatForm,
    ChangeUsernameForm, ChangePasswordForm  # ★ 2つのフォームをインポート
)

# --- アプリ設定 (変更なし) ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here_please_change'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'このページにアクセスするにはログインが必要です。'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- ログイン / 登録 / ホーム (変更なし) ---
@app.route('/')
@app.route('/home')
@login_required
def home():
    return render_template('home.html', title='ホーム')


@app.route('/utsumi')
def utsumi():
    return 'utsumi'


# ( ... login, register, logout ルートは変更なし ...)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    login_form = LoginForm()
    reg_form = RegistrationForm()
    if 'submit' in request.form:
        if request.form['submit'] == 'ログイン' and login_form.validate_on_submit():
            user = User.query.filter_by(username=login_form.username.data).first()
            if user is None or not user.check_password(login_form.password.data):
                flash('ユーザー名またはパスワードが無効です', 'danger')
                return redirect(url_for('login'))
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
    return render_template('login.html', title='ログイン', login_form=login_form, reg_form=reg_form)


@app.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('そのユーザー名は既に使用されています。', 'danger')
            return redirect(url_for('login'))

        # ★ 修正点: is_admin=False を明示的に指定
        user = User(username=form.username.data, is_admin=False)

        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('登録が完了しました。ログインしてください。', 'success')
        return redirect(url_for('login'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
        return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('login'))


# --- 災害機能 (変更なし) ---
# ( ... safety_check, emergency_sos, emergency_info, etc... ルートは変更なし ...)
@app.route('/safety-check', methods=['GET', 'POST'])
@login_required
def safety_check():
    form = SupportRequestForm()
    if form.validate_on_submit():
        new_request = SupportRequest(
            category=form.category.data,
            priority=form.priority.data,
            details=form.details.data,
            author=current_user
        )
        db.session.add(new_request)
        db.session.commit()
        flash('支援要請を送信しました。', 'success')
        return redirect(url_for('safety_check'))
    all_requests = SupportRequest.query.order_by(SupportRequest.timestamp.desc()).all()
    return render_template(
        'safety_check.html',
        title='安否確認・支援要請',
        form=form,
        requests=all_requests
    )


@app.route('/emergency-sos')
@login_required
def emergency_sos():
    return render_template('emergency_sos.html', title='緊急SOS発信')


@app.route('/send-sos', methods=['POST'])
@login_required
def send_sos():
    new_sos = SOSSignal(author=current_user)
    db.session.add(new_sos)
    db.session.commit()
    flash(f'SOS信号を送信しました。救助隊が確認します。', 'danger')
    return redirect(url_for('emergency_sos'))


@app.route('/emergency-info')
@login_required
def emergency_info():
    gov_alert = "[速報] 〇〇市全域に避難指示が発令されました。"
    return render_template('emergency_info.html', title='緊急情報', gov_alert=gov_alert)


@app.route('/shelter-info')
@login_required
def shelter_info():
    shelters = [
        {"name": "〇〇小学校体育館", "status": "空きあり (残り50名)", "status_color": "text-green-500"},
        {"name": "△△市民ホール", "status": "満室", "status_color": "text-red-500"}
    ]
    return render_template('shelter_info.html', title='避難場所空き情報', shelters=shelters)


@app.route('/realtime-info')
@login_required
def realtime_info():
    return render_template('realtime_info.html', title='リアルタイム情報')


@app.route('/hazard-map')
@login_required
def hazard_map():
    return render_template('hazard_map.html', title='ハザードマップ')


@app.route('/disaster-contacts')
@login_required
def disaster_contacts():
    contacts = [
        {"name": "災害対策本部", "number": "090-XXXX-XXXX"},
        {"name": "消防・救急", "number": "119"}
    ]
    return render_template('disaster_contacts.html', title='防災用連絡先', contacts=contacts)


@app.route('/map')
@login_required
def map():
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        flash('Google Maps APIキーが設定されていません。', 'danger')
    return render_template('map.html', title='マップ', api_key=api_key)


# ( ... chat, community, qr, group, group_chat ルートは変更なし ...)
@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    form = ChatForm()
    if form.validate_on_submit():
        new_msg = ChatMessage(
            text=form.message.data,
            author=current_user
        )
        db.session.add(new_msg)
        db.session.commit()
        return redirect(url_for('chat'))
    messages = ChatMessage.query.order_by(ChatMessage.timestamp.asc()).all()
    return render_template('chat.html', title='チャット', form=form, messages=messages)


@app.route('/community', methods=['GET', 'POST'])
@login_required
def community():
    form = CommunityPostForm()
    if form.validate_on_submit():
        new_post = CommunityPost(
            text=form.text.data,
            author=current_user
        )
        db.session.add(new_post)
        db.session.commit()
        flash('掲示板に投稿しました。', 'success')
        return redirect(url_for('community'))
    posts = CommunityPost.query.order_by(CommunityPost.timestamp.desc()).all()
    return render_template('community.html', title='コミュニティ', form=form, posts=posts)


@app.route('/qr')
@login_required
def qr_code():
    return render_template('qr.html', title='QRコード')


@app.route('/group', methods=['GET', 'POST'])
@login_required
def group_management():
    form = CreateGroupForm()
    if form.validate_on_submit():
        new_group = Group(name=form.name.data)
        db.session.add(new_group)
        new_group.members.append(current_user)
        db.session.commit()
        flash(f'グループ「{new_group.name}」を作成しました。', 'success')
        return redirect(url_for('group_management'))
    user_groups = current_user.groups
    return render_template('group_management.html',
                           title='グループ管理',
                           form=form,
                           groups=user_groups)


@app.route('/group/<int:group_id>/chat', methods=['GET', 'POST'])
@login_required
def group_chat(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user not in group.members:
        flash('このグループにアクセスする権限がありません。', 'danger')
        return redirect(url_for('group_management'))
    form = GroupChatForm()
    if form.validate_on_submit():
        new_msg = GroupChatMessage(
            text=form.message.data,
            author=current_user,
            group=group
        )
        db.session.add(new_msg)
        db.session.commit()
        return redirect(url_for('group_chat', group_id=group.id))
    messages = GroupChatMessage.query.filter_by(group_id=group.id).order_by(GroupChatMessage.timestamp.asc()).all()
    return render_template('group_chat.html',
                           title=f'{group.name} - チャット',
                           form=form,
                           group=group,
                           messages=messages)


# ★ ------------------------------------
# ★ ここが変更点です (POSTメソッド対応、フォーム処理追加)
# ★ ------------------------------------
@app.route('/settings', methods=['GET', 'POST'])  # 1. GET/POST許可
@login_required
def settings():
    """
    設定画面
    """
    # 2. 両方のフォームをインスタンス化
    username_form = ChangeUsernameForm()
    password_form = ChangePasswordForm()

    # 3. ユーザー名変更フォームの処理
    if username_form.validate_on_submit() and username_form.submit_username.data:
        new_username = username_form.username.data
        # ユーザー名の重複チェック
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('そのユーザー名は既に使用されています。', 'danger')
        else:
            current_user.username = new_username
            db.session.commit()
            flash('ユーザー名を変更しました。', 'success')
        return redirect(url_for('settings'))

    # 4. パスワード変更フォームの処理
    if password_form.validate_on_submit() and password_form.submit_password.data:
        # 古いパスワードが正しいかチェック
        if not current_user.check_password(password_form.old_password.data):
            flash('現在のパスワードが正しくありません。', 'danger')
        else:
            # 新しいパスワードを設定
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash('パスワードを変更しました。', 'success')
        return redirect(url_for('settings'))

    # 5. GETリクエスト時 (フォームをテンプレートに渡す)
    return render_template('settings.html',
                           title='設定',
                           username_form=username_form,
                           password_form=password_form)


# ★ ------------------------------------
# ★ 変更点ここまで
# ★ ------------------------------------


@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html', title='メニュー')


# --- DB初期化コマンド (変更なし) ---
@app.cli.command('init-db')
def init_db_command():
    db.create_all()
    print('データベースを初期化しました。')


if __name__ == '__main__':
    app.run(debug=True)