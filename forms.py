from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, RadioField
# EqualTo バリデータをインポート
from wtforms.validators import DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')


class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=4, max=100)])
    password = PasswordField('パスワード', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('新規登録')


class SupportRequestForm(FlaskForm):
    category = SelectField('要請カテゴリ (必須)',
                           choices=[
                               ('', '選択してください'),
                               ('food', '食料'),
                               ('water', '飲料水'),
                               ('medical', '医療/医薬品'),
                               ('shelter', '避難場所/毛布'),
                               ('other', 'その他')
                           ],
                           validators=[DataRequired()])
    priority = RadioField('優先度 (必須)',
                          choices=[
                              ('high', '高 (緊急)'),
                              ('medium', '中'),
                              ('low', '低')
                          ],
                          validators=[DataRequired()])
    details = TextAreaField('詳細な状況/数量',
                            validators=[Length(max=500)],
                            render_kw={"rows": 2, "placeholder": "..."})
    submit = SubmitField('支援要請を送信')


class ChatForm(FlaskForm):
    message = StringField('メッセージ',
                          validators=[DataRequired(), Length(max=500)],
                          render_kw={"placeholder": "メッセージを入力...", "autocomplete": "off"})
    submit = SubmitField('送信')

class CommunityPostForm(FlaskForm):
    text = TextAreaField('投稿内容',
                         validators=[DataRequired()],
                         render_kw={"rows": 3, "placeholder": "情報を入力..."})
    submit = SubmitField('投稿する')


class CreateGroupForm(FlaskForm):
    name = StringField('グループ名',
                       validators=[DataRequired(), Length(min=3, max=100)],
                       render_kw={"placeholder": "例: 家族グループ"})
    submit = SubmitField('作成する')

class GroupChatForm(FlaskForm):
    message = StringField('メッセージ',
                          validators=[DataRequired(), Length(max=500)],
                          render_kw={"placeholder": "メッセージを入力...", "autocomplete": "off"})
    submit = SubmitField('送信')


# ★ ------------------------------------
# ★ ここから2つのフォームを新規追加
# ★ ------------------------------------

class ChangeUsernameForm(FlaskForm):
    """ ユーザー名変更フォーム """
    username = StringField('新しいユーザー名',
                           validators=[DataRequired(), Length(min=4, max=100)])
    submit_username = SubmitField('ユーザー名を変更')

class ChangePasswordForm(FlaskForm):
    """ パスワード変更フォーム """
    old_password = PasswordField('現在のパスワード', validators=[DataRequired()])
    new_password = PasswordField('新しいパスワード',
                                 validators=[DataRequired(), Length(min=6)])
    new_password2 = PasswordField('新しいパスワード (確認)',
                                  validators=[DataRequired(),
                                              # 'new_password' フィールドと値が同じかチェック
                                              EqualTo('new_password', message='パスワードが一致しません。')])
    submit_password = SubmitField('パスワードを変更')

# ★ ------------------------------------
# ★ 追加ここまで
# ★ ------------------------------------