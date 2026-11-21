from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Імпортуємо всі наші моделі бази даних
from models import db, User, MediaItem, Review, ListEntry, ReviewLike, Comment, Report

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__name__))


app.config['SECRET_KEY'] = 'your-secret-key-for-session'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'media_service.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ініціалізація БД
db.init_app(app)

# Ініціалізація системи авторизації
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/')
def index():
    # Виводимо відгуки від новіших до старіших
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    reviews_count = Review.query.count()
    return render_template('index.html', reviews=reviews, reviews_count=reviews_count)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return "Користувач з таким ім'ям вже існує. Спробуйте інше.", 400
            
        new_user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
            
        return "Невірне ім'я або пароль. Спробуйте ще раз.", 401
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_review', methods=['POST'])
@login_required
def add_review():
    title = request.form.get('title')
    rating = request.form.get('rating')
    text = request.form.get('text')
    image = request.files.get('image')
    
    filename = None
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
    if title and rating and text:
        media = MediaItem.query.filter_by(title=title).first()
        if not media:
            media = MediaItem(title=title, image_filename=filename)
            db.session.add(media)
            db.session.commit()
        elif filename and not media.image_filename:
            media.image_filename = filename
            db.session.commit()
            
        new_review = Review(
            media_id=media.id, 
            user_id=current_user.id, 
            rating=int(rating), 
            text=text
        )
        db.session.add(new_review)
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id == current_user.id:
        db.session.delete(review)
        db.session.commit()
    return redirect(url_for('index'))



@app.route('/my_lists', methods=['GET', 'POST'])
@login_required
def my_lists():
    if request.method == 'POST':
        media_title = request.form.get('media_title')
        status = request.form.get('status')
        
        media = MediaItem.query.filter_by(title=media_title).first()
        if not media:
            media = MediaItem(title=media_title)
            db.session.add(media)
            db.session.commit()
            
        entry = ListEntry.query.filter_by(user_id=current_user.id, media_id=media.id).first()
        if entry:
            entry.status = status
        else:
            new_entry = ListEntry(user_id=current_user.id, media_id=media.id, status=status)
            db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('my_lists'))
        
    my_reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.created_at.desc()).all()
    my_planned = ListEntry.query.filter_by(user_id=current_user.id, status='Planned').all()
    my_watched = ListEntry.query.filter_by(user_id=current_user.id, status='Watched').all()
    
    return render_template('lists.html', reviews=my_reviews, planned=my_planned, watched=my_watched)

@app.route('/edit_review/<int:review_id>', methods=['POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id == current_user.id:
        review.text = request.form.get('text')
        review.rating = int(request.form.get('rating'))
        review.created_at = datetime.utcnow() # Оновлюємо час на поточний
        db.session.commit()
    return redirect(url_for('my_lists'))



@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    is_friend = False
    if current_user.is_authenticated and user in current_user.friends:
        is_friend = True
    return render_template('profile.html', user=user, is_friend=is_friend)

@app.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    bio = request.form.get('bio')
    avatar = request.files.get('avatar')
    
    if avatar and avatar.filename != '':
        filename = secure_filename(avatar.filename)
        avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_user.avatar_filename = filename
        
    current_user.bio = bio
    db.session.commit()
    return redirect(url_for('profile', username=current_user.username))

@app.route('/toggle_friend/<username>', methods=['POST'])
@login_required
def toggle_friend(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        return redirect(url_for('profile', username=username))
        
    if user in current_user.friends:
        current_user.friends.remove(user)
    else:
        current_user.friends.append(user)
        
    db.session.commit()
    return redirect(url_for('profile', username=username))



@app.route('/action/like/<int:review_id>', methods=['POST'])
@login_required
def like_review(review_id):
    like = ReviewLike.query.filter_by(user_id=current_user.id, review_id=review_id).first()
    if like:
        db.session.delete(like)
    else:
        new_like = ReviewLike(user_id=current_user.id, review_id=review_id)
        db.session.add(new_like)
    db.session.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/action/comment/<int:review_id>', methods=['POST'])
@login_required
def comment_review(review_id):
    text = request.form.get('text')
    if text:
        new_comment = Comment(user_id=current_user.id, review_id=review_id, text=text)
        db.session.add(new_comment)
        db.session.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/action/report/<int:review_id>', methods=['POST'])
@login_required
def report_review(review_id):
    reason = request.form.get('reason')
    if reason:
        new_report = Report(user_id=current_user.id, review_id=review_id, reason=reason)
        db.session.add(new_report)
        db.session.commit()
    return redirect(request.referrer or url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
