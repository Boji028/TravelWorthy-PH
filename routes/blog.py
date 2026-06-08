from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models.blog import BlogPost
from decorators import admin_required

blog_bp = Blueprint('blog', __name__)


@blog_bp.route('/')
def blog_list():
    category = request.args.get('category', '')
    query    = BlogPost.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    posts      = query.order_by(BlogPost.created_at.desc()).all()
    categories = db.session.query(BlogPost.category).filter(BlogPost.category != None).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('blog/list.html', posts=posts, categories=categories, active_category=category)


@blog_bp.route('/<int:post_id>')
def blog_detail(post_id):
    post         = db.get_or_404(BlogPost, post_id)
    recent_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.created_at.desc()).limit(3).all()
    return render_template('blog/detail.html', post=post, recent_posts=recent_posts)
