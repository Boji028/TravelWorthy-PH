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
    page  = max(1, request.args.get('page', 1, type=int) or 1)
    posts = query.order_by(BlogPost.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    categories = db.session.query(BlogPost.category).filter(
        BlogPost.category != None,
        BlogPost.is_published == True
    ).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('blog/list.html', posts=posts.items, categories=categories, active_category=category)


@blog_bp.route('/<int:post_id>')
def blog_detail(post_id):
    post = BlogPost.query.filter_by(id=post_id, is_published=True).first_or_404()
    recent_posts = BlogPost.query.filter(
        BlogPost.is_published == True,
        BlogPost.id != post_id
    ).order_by(BlogPost.created_at.desc()).limit(3).all()
    return render_template('blog/detail.html', post=post, recent_posts=recent_posts)
