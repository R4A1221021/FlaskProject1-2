# r4a1221021/flaskproject1-2/FlaskProject1-2-b35aea4865849d4948fb8a1e18280a969282046f/app.py

import os
import datetime
import io
import csv
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect

# --- モデルとフォームをインポート (修正) ---
from models import (
    db, User, SupportRequest, SOSSignal, ChatMessage, CommunityPost, Group, GroupChatMessage,
    Shelter # ShelterLog を削除
)
from forms import (
    LoginForm, RegistrationForm, SupportRequestForm,
    ChatForm, CommunityPostForm, CreateGroupForm, GroupChatForm,
    ChangeUsernameForm, ChangePasswordForm
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
    # SQLAlchemy 2.0 への移行を考慮し、Session.get() を使用
    return db.session.get(User, int(user_id))


# ★★★ 管理者専用デコレータの定義 ★★★
def admin_required(f):
    """ 管理者(is_admin=True)のみアクセスを許可するデコレータ """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.is_admin:
            flash('このページにアクセスする権限がありません。', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


# --- ログイン / 登録 / ホーム (変更なし、ただしエラーハンドリング等改善) ---
@app.route('/')
@app.route('/home')
@login_required
def home():
    return render_template('home.html', title='ホーム')

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
        elif request.form['submit'] == 'ログイン':
             for field, errors in login_form.errors.items():
                for error in errors:
                    flash(f"{getattr(login_form, field).label.text}: {error}", 'danger')
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
        user = User(username=form.username.data, is_admin=False)
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash('登録が完了しました。ログインしてください。', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {e}")
            flash('登録中にエラーが発生しました。', 'danger')
        return redirect(url_for('login'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
        login_form = LoginForm()
        return render_template('login.html', title='ログイン・ユーザー登録', login_form=login_form, reg_form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('login'))


# --- 災害機能 (shelter_info を修正) ---
@app.route('/safety-check', methods=['GET', 'POST'])
@login_required
def safety_check():
    form = SupportRequestForm()
    if form.validate_on_submit():
        try:
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
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Support request error: {e}")
            flash('支援要請の送信中にエラーが発生しました。', 'danger')
    try:
        all_requests = SupportRequest.query.options(db.joinedload(SupportRequest.author)).order_by(SupportRequest.timestamp.desc()).all()
    except Exception as e:
        app.logger.error(f"Error fetching support requests: {e}")
        all_requests = []
        flash('支援要請の読み込み中にエラーが発生しました。', 'danger')
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
    try:
        new_sos = SOSSignal(author=current_user)
        db.session.add(new_sos)
        db.session.commit()
        flash(f'SOS信号を送信しました。救助隊が確認します。', 'danger')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"SOS signal error: {e}")
        flash('SOS信号の送信中にエラーが発生しました。', 'danger')
    return redirect(url_for('emergency_sos'))

@app.route('/emergency-info')
@login_required
def emergency_info():
    gov_alert = "[速報] 〇〇市全域に避難指示が発令されました。"
    return render_template('emergency_info.html', title='緊急情報', gov_alert=gov_alert)

@app.route('/shelter-info')
@login_required
def shelter_info():
    shelter_data = []
    try:
        # DBから避難所名とキャパシティを取得 (修正)
        shelters = Shelter.query.with_entities(Shelter.name, Shelter.capacity).order_by(Shelter.name).all()
        for shelter in shelters:
            # 画像に合わせて名前とキャパシティのみ表示 (修正)
            shelter_data.append({
                "name": shelter.name,
                "status": f"キャパシティ: {shelter.capacity}人", # ステータス表示変更
                "status_color": "text-gray-700" # 色指定削除または固定
            })
    except Exception as e:
        app.logger.error(f"Error fetching shelter info: {e}")
        flash('避難所情報の読み込み中にエラーが発生しました。', 'danger')
    return render_template('shelter_info.html', title='避難場所情報', shelters=shelter_data) # title修正

@app.route('/realtime-info')
@login_required
def realtime_info():
    return render_template('realtime_info.htm.html', title='リアルタイム情報') # ファイル名注意

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
        flash('Google Maps APIキーが設定されていません。地図機能が制限される可能性があります。', 'warning')
    return render_template('map.html', title='マップ', api_key=api_key)


# --- コミュニケーション機能 (変更なし) ---
@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    form = ChatForm()
    if form.validate_on_submit():
        try:
            new_msg = ChatMessage(text=form.message.data, author=current_user)
            db.session.add(new_msg)
            db.session.commit()
            return redirect(url_for('chat'))
        except Exception as e:
            db.session.rollback(); app.logger.error(f"Chat message error: {e}"); flash('メッセージ送信エラー', 'danger')
    try:
        messages = ChatMessage.query.options(db.joinedload(ChatMessage.author)).order_by(ChatMessage.timestamp.asc()).all()
    except Exception as e:
        app.logger.error(f"Error fetching chat: {e}"); messages = []; flash('メッセージ読込エラー', 'danger')
    return render_template('chat.html', title='チャット', form=form, messages=messages)

@app.route('/community', methods=['GET', 'POST'])
@login_required
def community():
    form = CommunityPostForm()
    if form.validate_on_submit():
        try:
            new_post = CommunityPost(text=form.text.data, author=current_user)
            db.session.add(new_post); db.session.commit(); flash('投稿しました', 'success')
            return redirect(url_for('community'))
        except Exception as e:
            db.session.rollback(); app.logger.error(f"Community post error: {e}"); flash('投稿エラー', 'danger')
    try:
        posts = CommunityPost.query.options(db.joinedload(CommunityPost.author)).order_by(CommunityPost.timestamp.desc()).all()
    except Exception as e:
        app.logger.error(f"Error fetching community: {e}"); posts = []; flash('投稿読込エラー', 'danger')
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
        try:
            new_group = Group(name=form.name.data)
            db.session.add(new_group); db.session.flush()
            new_group.members.append(current_user); db.session.commit()
            flash(f'グループ「{new_group.name}」を作成', 'success'); return redirect(url_for('group_management'))
        except Exception as e:
            db.session.rollback(); app.logger.error(f"Group creation error: {e}"); flash('グループ作成エラー', 'danger')
    user_groups = current_user.groups
    return render_template('group_management.html', title='グループ管理', form=form, groups=user_groups)

@app.route('/group/<int:group_id>/chat', methods=['GET', 'POST'])
@login_required
def group_chat(group_id):
    group = db.session.get(Group, group_id)
    if not group: flash('グループが見つかりません', 'danger'); return redirect(url_for('group_management'))
    if current_user not in group.members: flash('アクセス権がありません', 'danger'); return redirect(url_for('group_management'))
    form = GroupChatForm()
    if form.validate_on_submit():
        try:
            new_msg = GroupChatMessage(text=form.message.data, author=current_user, group=group)
            db.session.add(new_msg); db.session.commit()
            return redirect(url_for('group_chat', group_id=group.id))
        except Exception as e:
            db.session.rollback(); app.logger.error(f"Group chat msg error: {e}"); flash('メッセージ送信エラー', 'danger')
    try:
        messages = GroupChatMessage.query.filter_by(group_id=group.id).options(db.joinedload(GroupChatMessage.author)).order_by(GroupChatMessage.timestamp.asc()).all()
    except Exception as e:
        app.logger.error(f"Error fetching group chat: {e}"); messages = []; flash('メッセージ読込エラー', 'danger')
    return render_template('group_chat.html', title=f'{group.name} - チャット', form=form, group=group, messages=messages)


# --- 設定・メニュー (変更なし) ---
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    username_form = ChangeUsernameForm()
    password_form = ChangePasswordForm()
    if request.method == 'POST':
        if 'submit_username' in request.form and username_form.validate_on_submit():
            new_username = username_form.username.data
            existing_user = User.query.filter(User.id != current_user.id, User.username == new_username).first()
            if existing_user: flash('そのユーザー名は既に使用されています', 'danger')
            else:
                try: current_user.username = new_username; db.session.commit(); flash('ユーザー名を変更しました', 'success')
                except Exception as e: db.session.rollback(); app.logger.error(f"Username change error: {e}"); flash('ユーザー名変更エラー', 'danger')
            return redirect(url_for('settings'))
        elif 'submit_password' in request.form and password_form.validate_on_submit():
            if not current_user.check_password(password_form.old_password.data): flash('現在のパスワードが違います', 'danger')
            else:
                try: current_user.set_password(password_form.new_password.data); db.session.commit(); flash('パスワードを変更しました', 'success')
                except Exception as e: db.session.rollback(); app.logger.error(f"Password change error: {e}"); flash('パスワード変更エラー', 'danger')
            return redirect(url_for('settings'))
    return render_template('settings.html', title='設定', username_form=username_form, password_form=password_form)

@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html', title='メニュー')


# ★★★ 管理者用ルート (修正) ★★★

@app.route('/admin')
@login_required
@admin_required
def admin_menu():
    """ 管理者メニュー画面 """
    return render_template('admin/menu.html', title='管理者メニュー')

@app.route('/admin/users')
@login_required
@admin_required
def admin_user_management():
    """ 登録ユーザー管理画面 """
    try:
        last_request_sq = db.session.query(SupportRequest.user_id, db.func.max(SupportRequest.timestamp).label('last_timestamp')).group_by(SupportRequest.user_id).subquery()
        users_with_last_seen = db.session.query(User, last_request_sq.c.last_timestamp).outerjoin(last_request_sq, User.id == last_request_sq.c.user_id).order_by(User.id).all()
    except Exception as e:
        app.logger.error(f"User management fetch error: {e}"); users_with_last_seen = []; flash('ユーザー情報取得失敗', 'danger')
    return render_template('admin/user_management.html', title='登録ユーザー管理', users=users_with_last_seen)

@app.route('/admin/sos_reports')
@login_required
@admin_required
def admin_sos_reports():
    """ SOSレポート確認画面 """
    try:
        reports = SupportRequest.query.options(db.joinedload(SupportRequest.author)).order_by(db.case( (SupportRequest.priority == 'high', 1), (SupportRequest.priority == 'medium', 2), (SupportRequest.priority == 'low', 3), else_=4), SupportRequest.timestamp.desc()).all()
    except Exception as e:
        app.logger.error(f"SOS reports fetch error: {e}"); reports = []; flash('SOSレポート取得失敗', 'danger')
    return render_template('admin/sos_reports.html', title='SOSレポート確認', reports=reports)

@app.route('/admin/export_csv')
@login_required
@admin_required
def admin_export_csv():
    """ SOSレポートをCSVエクスポート """
    try:
        reports = SupportRequest.query.options(db.joinedload(SupportRequest.author)).all()
        si = io.StringIO(); cw = csv.writer(si)
        cw.writerow(['ID', 'ユーザー名', 'カテゴリ', '優先度', '詳細', 'タイムスタンプ'])
        for report in reports:
            cw.writerow([report.id, report.author.username if report.author else 'N/A', report.category, report.priority, report.details, report.timestamp.strftime('%Y-%m-%d %H:%M:%S') if report.timestamp else ''])
        output = si.getvalue(); si.close()
        return Response(output, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=sos_reports.csv"})
    except Exception as e:
        app.logger.error(f"CSV Export error: {e}"); flash('CSVエクスポートエラー', 'danger'); return redirect(url_for('admin_sos_reports'))


# --- 修正: 避難所マスター管理ルート (シンプル版) ---
@app.route('/admin/shelters', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_shelter_management():
    """ 避難所を登録・管理する画面 (シンプル版) """
    if request.method == 'POST':
        name = request.form.get('name')
        capacity = request.form.get('capacity', type=int)
        if not name or not capacity or capacity <= 0:
            flash('避難所名と有効な収容可能人数は必須です。', 'danger')
            return redirect(url_for('admin_shelter_management'))
        if Shelter.query.filter_by(name=name).first():
            flash(f'避難所「{name}」は既に登録されています。', 'danger')
            return redirect(url_for('admin_shelter_management'))
        try:
            # シンプル化: name と capacity のみ
            new_shelter = Shelter(name=name, capacity=capacity)
            db.session.add(new_shelter)
            db.session.commit()
            flash(f'避難所「{name}」を登録しました。', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Shelter registration error: {e}")
            flash('避難所の登録中にエラーが発生しました。', 'danger')
        return redirect(url_for('admin_shelter_management'))
    # GETリクエスト時
    try:
        shelters = Shelter.query.order_by(Shelter.id.asc()).all()
    except Exception as e:
        app.logger.error(f"Error fetching shelters: {e}")
        shelters = []
        flash('避難所情報の取得に失敗しました。', 'danger')
    # テンプレート名を修正 (元の shelter_management.html を使う)
    return render_template('admin/shelter_management.html', title='避難所管理', shelters=shelters)

# --- 削除: 避難所受付ログ表示ルート ---
# @app.route('/admin/shelter_reports')... は削除


# --- DB初期化コマンド (変更なし) ---
@app.cli.command('init-db')
def init_db_command():
    """データベーステーブルを初期化（作成）するコマンド"""
    try:
        db.create_all()
        print('データベースを初期化しました。')
    except Exception as e:
        print(f"データベースの初期化中にエラーが発生しました: {e}")


if __name__ == '__main__':
    # host='0.0.0.0' を指定してローカルネットワークからアクセス可能に
    app.run(debug=True, host='0.0.0.0')