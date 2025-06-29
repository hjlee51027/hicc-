from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///board.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# DB 모델 (위에서 정의된 Post, Comment 클래스)
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    content = db.Column(db.Text, nullable=False)
    create_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "create_date": self.create_date.strftime("%Y-%m-%d")
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    create_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "create_date": self.create_date.strftime("%Y-%m-%d"),
            "post": self.post_id
        }

# DB 초기화 (애플리케이션 컨텍스트 내부에서 실행)
with app.app_context():
    db.create_all()

# 에러 핸들러
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        "status_code": 404,
        "error": "NOT_FOUND",
        "message": "요청한 리소스를 찾을 수 없습니다."
    }), 404

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({
        "status_code": 400,
        "error": "BAD_REQUEST",
        "message": "잘못된 요청입니다."
    }), 400


### 1. 게시글 전체 조회
@app.route('/api/posts', methods=['GET'])
def get_all_posts():
    posts = Post.query.all()
    return jsonify({"posts": [post.to_dict() for post in posts]}), 200

### 2. 게시글 작성
@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({
            "status_code": 400,
            "error": "BAD_REQUEST",
            "message": "제목과 내용을 모두 제공해야 합니다."
        }), 400

    title = data['title']
    content = data['content']

    if len(title) > 30:
        return jsonify({
            "status_code": 400,
            "error": "BAD_REQUEST",
            "message": "제목은 최대 30글자까지 입력 가능합니다."
        }), 400

    new_post = Post(title=title, content=content)
    db.session.add(new_post)
    db.session.commit()
    return jsonify({"message": "성공적으로 등록됐습니다."}), 200

### 3. 게시글 개별 조회
@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_single_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({
            "status_code": 404,
            "error": "POST_NOT_FOUND",
            "message": "존재하지 않는 게시글입니다."
        }), 404
    return jsonify(post.to_dict()), 200

### 4. 댓글 조회
@app.route('/api/posts/<int:post_id>/comment', methods=['GET'])
def get_comments_for_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({
            "status_code": 404,
            "error": "POST_NOT_FOUND",
            "message": "존재하지 않는 게시글입니다."
        }), 404

    comments = Comment.query.filter_by(post_id=post_id).all()
    return jsonify({"comments": [comment.to_dict() for comment in comments]}), 200

### 5. 댓글 작성
@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def create_comment_for_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({
            "status_code": 404,
            "error": "POST_NOT_FOUND",
            "message": "존재하지 않는 게시글입니다."
        }), 404

    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({
            "status_code": 400,
            "error": "BAD_REQUEST",
            "message": "댓글 내용을 제공해야 합니다."
        }), 400
    
    content = data['content']
    if len(content) > 200:
        return jsonify({
            "status_code": 400,
            "error": "BAD_REQUEST",
            "message": "댓글은 최대 200글자까지 입력 가능합니다."
        }), 400

    new_comment = Comment(content=content, post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({"message": "성공적으로 등록됐습니다."}), 200

if __name__ == '__main__':
    app.run(debug=True)