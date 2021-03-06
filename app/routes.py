import timeago,datetime
import os
import secrets
from PIL import Image
from flask import render_template,redirect,request,url_for,flash,abort,jsonify
from app import app,db,bcrypt,mail
from app.models import Subscribers, Users,Articles,Articlecomments,Videocomments,Categories,Tags,Videos
from flask_login import login_user,current_user,logout_user,login_required
from app.forms import (RegistrationForm,LoginForm,UpdateAccountForm,
PostForm,RequestResetForm,ResetPasswordForm,ContactForm,CommentsForm,
SendNotificationsForm,AuthorRegistrationForm,AuthorUpdateAccountForm,VideoForm,SubscribeForm)
from flask_mail import Message


@app.route('/')
def index():
    articles = Articles.query.order_by(Articles.date_posted.desc()).limit(5).all()
    headline = Articles.query.order_by(Articles.date_posted.desc()).first_or_404()
    now = datetime.datetime.now() 
    time_posted = timeago.format(headline.date_posted, now)
    latest_news = Articles.query.order_by(Articles.date_posted.desc()).limit(3).all()
    popular = Articles.query.order_by(Articles.date_posted.desc()).limit(3).all()
    random_articles = Articles.query.filter_by(category_id=1).order_by(Articles.date_posted.desc()).limit(5).all()
    headline_random = Articles.query.filter_by(category_id=1).order_by(Articles.date_posted.desc()).first()
    trending_news = Articles.query.order_by(Articles.date_posted.desc()).limit(5).all()
    categories = Categories.query.all()
    first_row_videos = Videos.query.order_by(Videos.date_posted.desc()).limit(2).all()
    second_row_videos = Videos.query.order_by(Videos.date_posted.desc()).offset(2).limit(2).all()
    third_row_videos = Videos.query.order_by(Videos.date_posted.desc()).offset(4).limit(2).all()
    latest_videos = Videos.query.order_by(Videos.date_posted.desc()).limit(8).all()
    return render_template('index.html',articles = articles,latest_news=latest_news,
    headline=headline,categories=categories,first_row_videos=first_row_videos,third_row_videos=third_row_videos,
    latest_videos=latest_videos,trending_news=trending_news,second_row_videos=second_row_videos,
    popular=popular,random_articles=random_articles,headline_random=headline_random,time_posted=time_posted)

@app.route('/login', methods = ['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember.data)
            flash('You have been successfully logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Email or password incorrect!','danger')
    return render_template('login.html', title = 'Login', form = form)

@app.route('/register', methods = ['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        newuser = Users(email=form.email.data,username=form.username.data,password=hashed_password)
        db.session.add(newuser)
        db.session.commit()

        flash('Registered successfully! Login to access your account.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Register', form = form)

@app.route('/write_for_us', methods = ['GET','POST'])
@login_required
def writer_register():
    if current_user.post_author == True:
        return redirect(url_for('index'))
    form = AuthorRegistrationForm()
    if form.validate_on_submit():
        current_user.bio = form.bio.data
        current_user.address = form.address.data
        current_user.phone = form.phone.data
        current_user.city = form.city.data
        current_user.facebook = form.facebook.data
        current_user.instagram = form.instagram.data
        current_user.twitter = form.twitter.data
        current_user.youtube = form.youtube.data
        current_user.post_author = True
        db.session.commit()

        flash('Successfully registered as an author!', 'success')
        return redirect(url_for('login'))
    return render_template('author_register.html', title = 'Write for us', form = form)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _,f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/imgs/profile_pics', picture_fn)

    output_size = (250, 250)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(picture_path)
    return picture_fn


@app.route('/img_upload', methods=['POST'])
@login_required
def img_uploader():
    img = request.files.get('file')
    random_hex = secrets.token_hex(8)
    _,f_ext = os.path.splitext(img.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/imgs/post_imgs', picture_fn)

    output_size = (250, 250)
    i = Image.open(img)
    i.thumbnail(output_size)
    i.save(picture_path)

    pic_location = url_for('static', filename = 'imgs/post_imgs/' + picture_fn)
    return jsonify({'location': pic_location})

@app.route('/account', methods = ['GET','POST'])
@login_required
def account():
    if current_user.admin == True:
        return redirect(url_for('admin_account'))
    if current_user.post_author == True:
        return redirect(url_for('author_account'))
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.profile_pic = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account info has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename = 'imgs/profile_pics/' + current_user.profile_pic)
    return render_template('account.html', title = current_user.username, profile_pic = image_file, form = form)


@app.route('/author_account', methods = ['GET','POST'])
@login_required
def author_account():
    if current_user.admin == True:
        return redirect(url_for('admin_account'))
    if current_user.post_author == False:
        return redirect(url_for('account'))
    form = AuthorUpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.profile_pic = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        current_user.address = form.address.data
        current_user.phone_number = form.phone.data
        current_user.city = form.city.data
        current_user.facebook = form.facebook.data
        current_user.instagram = form.instagram.data
        current_user.twitter = form.twitter.data
        current_user.youtube = form.youtube.data
        db.session.commit()
        flash('Account info has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
        form.address.data = current_user.address
        form.phone.data = current_user.phone_number
        form.city.data = current_user.city
        form.facebook.data = current_user.facebook
        form.instagram.data = current_user.instagram
        form.twitter.data = current_user.twitter
        form.youtube.data = current_user.youtube
    image_file = url_for('static', filename = 'imgs/profile_pics/' + current_user.profile_pic)
    return render_template('author_account.html', title = current_user.username, profile_pic = image_file, form = form)

def send_email_to_admin(email,message):
    msg = Message(f'Email from {email}', 
                   sender=email,
                   recipients=['smuminaetx100@gmail.com'])
    msg.body = f'''
{message}
'''
    mail.send(msg)

@app.route('/subscribe', methods = ['GET','POST'])
def subscribe():
    form = SubscribeForm()
    if form.validate_on_submit():
        subscriber = Subscribers(email=form.email.data)
        db.session.add(subscriber)
        db.session.commit()
        flash('You have successfully subscribed to our newsletter', 'success')
        return redirect(url_for('index'))
    return render_template('subscribe.html',form=form)

@app.route('/contact', methods = ['GET','POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        email = form.email.data
        message = form.message.data
        send_email_to_admin(email,message)
        flash('Your email has been sent!','info')
    return render_template('contact.html',title='Contact us', form = form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# videos
@app.route('/newvideo', methods = ['GET', 'POST'])
@login_required
def new_video():
    if current_user.post_author == False:
        abort(404)
    form =VideoForm()
    form.category.choices = [(category.id, category.categoryname) for category in Categories.query.all()]
    if form.validate_on_submit():
        video = Videos(title=form.title.data,category_id=form.category.data
        ,vid_author=current_user,video_url=form.video_url.data,video_desc=form.video_desc.data)
        db.session.add(video)
        db.session.commit()
        flash('Your video has been posted successfully!', 'success')
        return redirect(url_for('video',id=video.id))
    return render_template('new_video.html', title = 'New video',form=form,legend='Post new article')

@app.route('/video/<int:id>', methods = ['GET', 'POST'])
def video(id):
    video = Videos.query.get_or_404(id)
    now = datetime.datetime.now() 
    time_posted = timeago.format(video.date_posted, now)
    related_videos = Videos.query.filter_by(category=video.category).order_by(Videos.date_posted.desc()).limit(4).all()
    latest_vid = Videos.query.order_by(Videos.date_posted.desc()).limit(4).all()
    trending_vid = Videos.query.order_by(Videos.date_posted.desc()).limit(4).all()
    comments = video.userscomments

    form = CommentsForm()
    if form.validate_on_submit():
        comment = Videocomments(comment=form.comments.data,user_id=current_user.id,video_id=video.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your have successfully added your comment!', 'success')
        return redirect(url_for('video',id = id))
    return render_template('video.html', title=video.title, video = video,form=form,date_posted=time_posted,
    related_videos=related_videos,latest_vid=latest_vid,trending_vid=trending_vid,comments=comments)


@app.route('/video/<int:id>/update', methods = ['GET', 'POST'])
@login_required
def updatevid(id):
    video = Videos.query.get_or_404(id)
    if video.vid_author != current_user:
        abort(404)

    form = VideoForm()
    form.category.choices = [(category.id, category.categoryname) for category in Categories.query.all()]
    if form.validate_on_submit():
        video.title = form.title.data
        video.category_id = form.category.data
        video.video_url = form.video_url.data
        video.video_desc = form.video_desc.data
        db.session.commit()
        flash('Your video has been updated!', 'success')
        return redirect(url_for('video',id = video.id))
    elif request.method == 'GET':
        form.title.data = video.title
        form.video_url.data = video.video_url
        form.video_desc.data = video.video_desc
    return render_template('new_video.html', title = 'Update video', form = form, legend = 'Update video')


@app.route('/video/<int:id>/delete', methods = ['POST'])
@login_required
def deletevideo(id):
    video = Videos.query.get_or_404(id)
    if video.vid_author != current_user:
        abort(404)

    db.session.delete(video)
    db.session.commit()
    flash('Your video has been deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/vid_author/<string:username>')
def author_videos(username):
    page = request.args.get('page', 1, type=int)
    user = Users.query.filter_by(username=username).first_or_404()
    videos = Videos.query.filter_by(vid_author=user)\
        .order_by(Videos.date_posted.desc())\
        .paginate(per_page=20, page=page)
    return render_template('author_videos.html',videos = videos, user=user)


@app.route('/vid_category/<int:category_id>')
def vid_categories(category_id):
    page = request.args.get('page', 1, type=int)
    category = Categories.query.get_or_404(category_id)
    videos = Videos.query.filter_by(category=category).order_by(Videos.date_posted.desc())\
    .paginate(per_page=20, page=page)
    latest = Videos.query.filter_by(category=category).order_by(Videos.date_posted.desc()).limit(5).all()
    trending = Videos.query.filter_by(category=category).order_by(Videos.date_posted.desc()).limit(5).all()
    return render_template('pages/vid_categories.html',videos = videos,category=category,latest=latest,trending=trending)


@app.route('/video/<videoid>/comment/<int:commentid>/update', methods = ['GET', 'POST'])
@login_required
def updatevidcomment(commentid,videoid):
    video = Videos.query.get_or_404(int(videoid))
    comment = Videocomments.query.get_or_404(int(commentid))
    if comment.its_writer != current_user:
        abort(404)

    form = CommentsForm()
    if form.validate_on_submit():
        comment.comment = form.comments.data
        db.session.commit()
        flash('Your comment has been updated!', 'success')
        return redirect(url_for('video',id = video.id))
    elif request.method == 'GET':
        form.comments.data = comment.comment
    return render_template('video.html', title = 'Update video comment', form = form,video=video)

@app.route('/video/<int:videoid>/comment/<int:commentid>/delete', methods = ['POST'])
@login_required
def deletevidcomment(videoid,commentid):
    video = Videos.query.get_or_404(videoid)
    comment = Videocomments.query.get_or_404(commentid)
    if comment.its_writer != current_user:
        abort(404)

    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('video',id=video.id))



# posts
@app.route('/newpost', methods = ['GET', 'POST'])
@login_required
def new_post():
    if current_user.post_author == False:
        abort(404)
    form =PostForm()
    form.category.choices = [(category.id, category.categoryname) for category in Categories.query.all()]
    if form.validate_on_submit():
        article = Articles(title=form.title.data,category_id=form.category.data,
        content=form.content.data,author=current_user,cover_img=form.cover_picture.data,
        pic_desc=form.pic_desc.data)
        db.session.add(article)
        db.session.commit()
        flash('Your post has been posted successfully!', 'success')
        return redirect(url_for('post',id=article.id))
    return render_template('new_posts.html', title = 'New post',form=form)


@app.route('/<int:id>', methods = ['GET', 'POST'])
def post(id):
    article = Articles.query.get_or_404(id)
    tags = Tags.query.filter_by(its_category=article.category).all()
    image = article.cover_img
    img_desc = article.pic_desc
    article_tags = article.its_tags
    related_posts = Articles.query.filter_by(category=article.category).order_by(Articles.date_posted.desc()).limit(6).all()
    latest_posts = Articles.query.order_by(Articles.date_posted.desc()).limit(4).all()
    trending_posts = Articles.query.order_by(Articles.date_posted.desc()).limit(4).all()
    comments = article.users_comments
    now = datetime.datetime.now() 
    time_posted = timeago.format(article.date_posted, now)

    form = CommentsForm()
    if form.validate_on_submit():
        comment = Articlecomments(comment=form.comments.data,user_id=current_user.id,article_id=article.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your have successfully added your comment!', 'success')
        return redirect(url_for('post',id = id))
    return render_template('post.html', title=article.title, article = article,
    form=form,posts=related_posts,comments=comments,time_posted=time_posted,image=image,
    img_desc=img_desc,tags=article_tags,latest_posts=latest_posts,trending_posts=trending_posts,all_tags=tags)

@app.route('/post/<int:id>/update', methods = ['GET', 'POST'])
@login_required
def updatepost(id):
    article = Articles.query.get_or_404(id)
    if article.author != current_user:
        abort(404)

    form = PostForm()
    form.category.choices = [(category.id, category.categoryname) for category in Categories.query.all()]
    if form.validate_on_submit():
        article.title = form.title.data
        article.category_id = form.category.data
        article.cover_img = form.cover_picture.data
        article.pic_desc = form.pic_desc.data
        article.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post',id = article.id))
    elif request.method == 'GET':
        form.title.data = article.title
        form.cover_picture.data = article.cover_img
        form.pic_desc.data = article.pic_desc
        form.content.data = article.content
    return render_template('new_posts.html', title = 'Update post', form = form, legend = 'Update post')


@app.route('/post/<int:id>/delete', methods = ['POST'])
@login_required
def deletepost(id):
    article = Articles.query.get_or_404(id)
    if article.author != current_user:
        abort(404)

    db.session.delete(article)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/author/<string:username>')
def author_posts(username):
    page = request.args.get('page', 1, type=int)
    user = Users.query.filter_by(username=username).first_or_404()
    articles = Articles.query.filter_by(author=user)\
        .order_by(Articles.date_posted.desc())\
        .paginate(per_page=20, page=page)
    return render_template('author_posts.html',articles = articles, user=user)


@app.route('/category/<int:category_id>')
def categories(category_id):
    page = request.args.get('page', 1, type=int)
    category = Categories.query.get_or_404(category_id)
    articles = Articles.query.filter_by(category=category).order_by(Articles.date_posted.desc())\
    .paginate(per_page=20, page=page)
    latest = Articles.query.filter_by(category=category).order_by(Articles.date_posted.desc()).limit(5).all()
    trending = Articles.query.filter_by(category=category).order_by(Articles.date_posted.desc()).limit(5).all()
    return render_template('pages/categories.html',articles = articles,category=category,latest=latest,trending=trending)

@app.route('/post/<int:id>/add_tag/<int:tagid>', methods = ['POST'])
def add_tags(id,tagid):
    article = Articles.query.get_or_404(id)
    tag = Tags.query.get_or_404(tagid)
    article.its_tags.append(tag)
    db.session.commit()
    flash('Tag(s) added successfully', 'success')
    return redirect(url_for('post',id=article.id))

@app.route('/post/<int:id>/remove_tag/<int:tagid>', methods = ['POST'])
def remove_tags(id,tagid):
    article = Articles.query.get_or_404(id)
    tag = Tags.query.get_or_404(tagid)
    article.its_tags.remove(tag)
    db.session.commit()
    flash('Tag(s) removed successfully', 'success')
    return redirect(url_for('post',id=article.id))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', 
                   sender='smuminaetx100@gmail.com',
                   recipients=[user.email])
    msg.body = f'''To reset your password, click the link below:
{url_for('reset_token',token=token,_external = True)}
Token expires within one hour!
If you did not make this request simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route('/reset_password', methods = ['GET','POST'])
def reset_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email = form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title = 'Reset Password', form = form)

@app.route('/reset_password/<token>', methods = ['GET','POST'])
def reset_token(token):
    user = Users.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token!', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been updated! You are now able to login and access your account', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title = 'Reset Password', form = form)


@app.route('/search')
def search():
    article_page = request.args.get('page', 1, type=int)
    vid_page = request.args.get('page', 1, type=int)
    search_value = request.args.get('search_string')
    search = "%{0}%".format(search_value)
    article_results = Articles.query.filter(db.or_(Articles.title.like(search),
    Articles.content.like(search),Articles.pic_desc.like(search)))\
    .order_by(Articles.date_posted.desc())\
    .paginate(per_page=20, page=article_page)
    vid_results = Videos.query.filter(db.or_(Videos.title.like(search),
    Videos.video_desc.like(search)))\
    .order_by(Videos.date_posted.desc())\
    .paginate(per_page=20, page=vid_page)
    return render_template('pages/search_results.html',article_results=article_results,
    search_value=search_value,vid_results=vid_results)
    

@app.route('/post/<articleid>/comment/<int:commentid>/update', methods = ['GET', 'POST'])
@login_required
def updatecomment(commentid,articleid):
    article = Articles.query.get_or_404(int(articleid))
    comment = Articlecomments.query.get_or_404(int(commentid))
    if comment.writer != current_user:
        abort(404)

    form = CommentsForm()
    if form.validate_on_submit():
        comment.comment = form.comments.data
        db.session.commit()
        flash('Your comment has been updated!', 'success')
        return redirect(url_for('post',id = article.id))
    elif request.method == 'GET':
        form.comments.data = comment.comment
    return render_template('post.html', title = 'Update comment', form = form,article=article)

@app.route('/post/<int:articleid>/comment/<int:commentid>/delete', methods = ['POST'])
@login_required
def deletecomment(articleid,commentid):
    article = Articles.query.get_or_404(articleid)
    comment = Articlecomments.query.get_or_404(commentid)
    if comment.writer != current_user:
        abort(404)

    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('post',id=article.id))



@app.route('/terms_and_conditions')
def terms_conditions():
    return render_template('Terms_and_conditions.html', title='Terms and conditions')

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html', title='Privacy policy')

@app.route('/tag/<int:tagid>')
def tags(tagid):
    page = request.args.get('page', 1, type=int)
    tag = Tags.query.get_or_404(tagid)
    tag_articles = tag.articles
    category_id = tag.category_id
    category = Categories.query.get_or_404(category_id)
    articles = Articles.query.filter_by(category=category).order_by(Articles.date_posted.desc())\
    .paginate(per_page=20, page=page)
    latest = Articles.query.filter_by(category=category).order_by(Articles.date_posted.desc()).limit(5).all()
    trending = Articles.query.filter_by(category=category).order_by(Articles.date_posted.desc()).limit(5).all()
    return render_template('pages/tags.html',articles = articles,title=tag.tagname,tag=tag,latest=latest,
    trending=trending,tag_articles=tag_articles)



# Admin routes
@app.route('/admin')
@login_required
def admin():
    if current_user.admin != True:
        abort(404)
    users = Users.query.paginate()
    articles = Articles.query.paginate()
    comments = Articlecomments.query.paginate()
    image_file = url_for('static', filename = 'imgs/profile_pics/' + current_user.profile_pic)
    return render_template('admin/home.html',users=users,articles=articles,comments=comments,image_file=image_file)

@app.route('/adminaccount', methods = ['GET','POST'])
def admin_account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.profile_pic = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account info has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename = 'imgs/profile_pics/' + current_user.profile_pic)
    return render_template('admin/admin_account.html', title = current_user.username, profile_pic = image_file, form = form)

@app.route('/all_comments')
@login_required
def comments():
    comments = Articlecomments.query.all()
    return render_template('admin/comments.html', comments = comments)

@app.route('/delete_comment/<int:commentid>')
@login_required
def admin_delete_comment(commentid):
    message = 'Your comment was deleted because of:'
    comment = Articlecomments.query.get_or_404(int(commentid))
    user = comment.writer
    db.session.delete(comment)
    db.session.commit()
    flash('The comment has been deleted!', 'success')
    send_user_email(user,message)
    return redirect(url_for('comments'))

@app.route('/all_admins')
@login_required
def all_admins():
    admins = Users.query.filter_by(admin=True).paginate()
    for admin in admins.items:
        image_file = url_for('static', filename = 'imgs/profile_pics/' + admin.profile_pic)
    return render_template('admin/all_admins.html', admins = admins, image_file = image_file, title='Site admins')

@app.route('/settings')
@login_required
def settings():
    return render_template('admin/settings.html')

@app.route('/notifications', methods=['GET','POST'])
@login_required
def notifications():
    form = SendNotificationsForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        send_user_email(user,form.notification.data)
        flash('Notification sent successfully','success')
    return render_template('admin/notifications.html',form=form)


@app.route('/all_users')
@login_required
def all_users():
    users = Users.query.paginate()
    for user in users.items:
        image_file = url_for('static',filename='imgs/profile_pics/' + user.profile_pic)
    return render_template('admin/users.html', users = users, image_file=image_file,title='All users')

@app.route('/all_posts')
@login_required
def all_posts():
    posts = Articles.query.paginate()
    return render_template('admin/all_posts.html', posts = posts)

def send_user_email(user,message):
    msg = Message('Email from admin of Blog', 
                   sender= 'smuminaetx100@gmail.com',
                   recipients=[user.email])
    msg.body = f'''
{message}
'''
    mail.send(msg)


@app.route('/send_user_email/<int:id>/<string:message>')
@login_required
def send_user_email(id,message):
    user = Users.query.get_or_404(str(id))
    message = message
    if user:
        send_user_email(user,message)
    flash('User does not exist!')
    return render_template('admin/users.html')

