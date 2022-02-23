#!/usr/bin/python3
import json
import uuid
from datetime import datetime
from fastapi import APIRouter
from sqlalchemy import and_

from ..form_types import (
    PoemAddForm,
    PoemUpdateForm,
    PoemLikeForm,
    PoemDeleteForm
)
from ..database import get_session, User, Comment, Poem, PoemLike, UserFollowing
from ..utils.token_handlers import AuthToken
from ..utils.pagination import extract_page


router = APIRouter(prefix='/api/v1')


@router.get('/poem')
async def get_poem(id: str, token: str):
    response = {
        'success': False,
        'message': 'Failed to find poem.'
    }
    auth_token = AuthToken.decode(token)
    user_id = auth_token.user_id if auth_token is not None else None
    db_session = get_session()
    try:
        poem = db_session.query(
            Poem).filter(
                Poem.id == id).first()
        if poem:
            user = db_session.query(
                User).filter(User.id == poem.user_id).first()
            if not user:
                return response
            comments = db_session.query(
                Comment).filter(
                    Comment.poem_id == id).all()
            comments_count = len(comments) if comments else 0
            likes = db_session.query(
                PoemLike).filter(
                    PoemLike.poem_id == id).all()
            likes_count = len(likes) if likes else 0
            is_liked_by_user = False
            if user_id:
                poem_interaction = db_session.query(
                    PoemLike).filter(and_(
                        PoemLike.poem_id == id,
                        PoemLike.user_id == user_id
                    )).first()
                if poem_interaction:
                    is_liked_by_user = True
            response = {
                'success': True,
                'data': {
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'profilePhotoId': user.profile_photo_id
                    },
                    'id': poem.id,
                    'title': poem.title,
                    'publishedOn': poem.created_on.isoformat(),
                    'verses': json.JSONDecoder().decode(poem.text),
                    'commentsCount': comments_count,
                    'likesCount': likes_count,
                    'isLiked': is_liked_by_user
                }
            }
    finally:
        db_session.close()
    return response


@router.post('/poem')
async def add_poem(body: PoemAddForm):
    response = {
        'success': False,
        'message': 'Failed to add poem.'
    }
    auth_token = AuthToken.decode(body.authToken)
    wrong_conditions = [
        auth_token is None,
        auth_token is not None and (auth_token.user_id != body.userId),
        len(body.title) > 256,
        len(body.verses) < 1,
        not all(list(map(lambda x: len(x.strip()) > 5, body.verses)))
    ]
    if any(wrong_conditions):
        return response
    db_session = get_session()
    try:
        gen_id = str(uuid.uuid4())
        cur_time = datetime.utcnow()
        poem = Comment(
            id=gen_id,
            created_on=cur_time,
            updated_on=cur_time,
            user_id=body.userId,
            title=body.title,
            text=json.JSONEncoder().encode(body.verses)
        )
        db_session.add(poem)
        db_session.commit()
        response = {
            'success': True,
            'data': {
                'id': gen_id,
                'createdOn': cur_time.isoformat(),
                'repliesCount': 0,
                'likesCount': 0
            }
        }
    except Exception as ex:
        print(ex.args[0])
        db_session.rollback()
    finally:
        db_session.close()
    return response


@router.put('/poem')
async def update_poem(body: PoemUpdateForm):
    response = {
        'success': False,
        'message': 'Failed to update poem.'
    }
    auth_token = AuthToken.decode(body.authToken)
    wrong_conditions = [
        auth_token is None,
        auth_token is not None and (auth_token.user_id != body.userId),
        len(body.title) > 256,
        len(body.verses) < 1,
        not all(list(map(lambda x: len(x.strip()) > 5, body.verses)))
    ]
    if any(wrong_conditions):
        return response
    db_session = get_session()
    try:
        cur_time = datetime.utcnow()
        db_session.query(Poem).filter(Poem.id == body.poemId).update(
            {
                Poem.title: body.title,
                Poem.updated_on: cur_time,
                Poem.text: json.JSONEncoder().encode(body.verses)
            },
            synchronize_session=False
        )
        db_session.commit()
        response = {
            'success': True,
            'data': {}
        }
    except Exception as ex:
        print(ex.args[0])
        db_session.rollback()
    finally:
        db_session.close()
    return response


@router.delete('/poem-comments')
async def remove_user(body: PoemDeleteForm):
    response = {
        'success': False,
        'message': 'Failed to remove poem.'
    }
    auth_token = AuthToken.decode(body.authToken)
    if auth_token is None or auth_token.user_id != body.userId:
        return response
    db_session = get_session()
    try:
        db_session.query(Poem).filter(and_(
                Poem.poem_id == body.poemId,
                Poem.user_id == body.userId,
        )).delete(
            synchronize_session=False
        )
        db_session.query(Comment).filter(and_(
                Comment.poem_id == body.poemId,
                Comment.id == body.commentId,
        )).delete(
            synchronize_session=False
        )
        db_session.commit()
        response = {
            'success': True,
            'data': {}
        }
    finally:
        db_session.close()
    return response


@router.put('/like-poem')
async def like_poem(body: PoemLikeForm):
    response = {
        'success': False,
        'message': 'Failed to like poem.'
    }
    auth_token = AuthToken.decode(body.authToken)
    wrong_conditions = [
        auth_token is None,
        auth_token is not None and (auth_token.user_id != body.userId),
        len(body.title) > 256,
        len(body.verses) < 1,
        not all(list(map(lambda x: len(x.strip()) > 5, body.verses)))
    ]
    if any(wrong_conditions):
        return response
    db_session = get_session()
    try:
        cur_usr_fav = db_session.query(
            PoemLike).filter(
                and_(
                    PoemLike.user_id == auth_token.user_id,
                    PoemLike.poem_id == body.poemId,
            )).first()
        if cur_usr_fav:
            db_session.query(PoemLike).filter(and_(
                    PoemLike.user_id == auth_token.user_id,
                    PoemLike.poem_id == body.poemId,
            )).delete(
                synchronize_session=False
            )
            db_session.commit()
            response = {
                'success': True,
                'data': {'status': False}
            }
        else:
            new_favourite = PoemLike(
                id=str(uuid.uuid4()),
                created_on=datetime.utcnow(),
                user_id=body.userId,
                poem_id=body.poemId,
                name=body.name
            )
            db_session.add(new_favourite)
            db_session.commit()
            response = {
                'success': True,
                'data': {'status': True}
            }
    except Exception as ex:
        print(ex.args[0])
        db_session.rollback()
    finally:
        db_session.close()
    return response


@router.get('/user-poems')
async def get_user_poems(
    userId='',
    token='',
    span=12,
    after='',
    before=''
    ):
    response = {
        'success': False,
        'message': 'Failed to find poems of the user.'
    }
    if span < 0:
        span = -span
    if not userId:
        return response
    auth_token = AuthToken.decode(token)
    user_id = auth_token.user_id if auth_token is not None else None
    db_session = get_session()
    try:
        result = db_session.query(
            Poem).filter(
                Poem.user_id == userId).all()
        new_result = []
        if result is not None:
            user = db_session.query(
                User).filter(User.id == userId).first()
            if not user:
                return response
            for item in result:
                comments = db_session.query(
                    Comment).filter(
                        Comment.poem_id == item.id).all()
                comments_count = len(comments) if comments else 0
                likes = db_session.query(
                    PoemLike).filter(
                        PoemLike.poem_id == item.id).all()
                likes_count = len(likes) if likes else 0
                is_liked_by_user = False
                if user_id:
                    poem_interaction = db_session.query(
                        PoemLike).filter(and_(
                            PoemLike.poem_id == item.id,
                            PoemLike.user_id == user_id
                        )).first()
                    if poem_interaction:
                        is_liked_by_user = True
                obj = {
                    'id': item.id,
                    'title': item.title,
                    'publishedOn': item.created_on.isoformat(),
                    'verses': json.JSONDecoder().decode(item.text),
                    'commentsCount': comments_count,
                    'likesCount': likes_count,
                    'isLiked': is_liked_by_user
                }
                new_result.append(obj)
        response = {
            'success': True,
            'data': extract_page(
                new_result,
                span,
                after,
                before,
                False,
                lambda x: x['id']
            )
        }
    finally:
        db_session.close()
    return response


# TODO: Work on this feature
@router.get('/poems-channel')
async def get_channel_poems(
    token='',
    span=12,
    after='',
    before=''
    ):
    response = {
        'success': False,
        'message': 'Failed to find poems for the channel.'
    }
    if span < 0:
        span = -span
    if not token:
        return response
    auth_token = AuthToken.decode(token)
    user_id = auth_token.user_id if auth_token is not None else None
    db_session = get_session()
    try:
        followings = db_session.query(
            UserFollowing).filter(UserFollowing.follower_id == user_id).all()
        new_result = []
        if followings:
            followings = list(map(lambda x: x.following_id, followings))
            followings.append(user_id)
            followings_poems = []
            for id in followings:
                poems = db_session.query(
                    Poem).filter(
                        Poem.user_id == id).all()
                user = db_session.query(
                    User).filter(User.id == id).first()
                user_poems = []
                for poem in poems:
                    comments = db_session.query(
                        Comment).filter(and_(
                                Comment.poem_id == poem.id,
                                Comment.comment_id == None
                            )).all()
                    comments_count = len(comments) if comments else 0
                    likes = db_session.query(
                        PoemLike).filter(
                            PoemLike.poem_id == poem.id).all()
                    likes_count = len(likes) if likes else 0
                    is_liked_by_user = False
                    if user_id:
                        poem_interaction = db_session.query(
                            PoemLike).filter(and_(
                                PoemLike.poem_id == poem.id,
                                PoemLike.user_id == user_id
                            )).first()
                        if poem_interaction:
                            is_liked_by_user = True
                    obj = {
                        'id': item.id,
                        'title': item.title,
                        'publishedOn': item.created_on.isoformat(),
                        'verses': json.JSONDecoder().decode(item.text),
                        'commentsCount': comments_count,
                        'likesCount': likes_count,
                        'isLiked': is_liked_by_user
                    }
                    user_poems.append(obj)
                followings_poems.append(
                    {
                        'user': {
                            'id': user.id,
                            'name': user.name,
                            'profilePhotoId': user.profile_photo_id
                        },
                        'poems': user_poems
                    }
                )
        response = {
            'success': True,
            'data': extract_page(
                new_result,
                span,
                after,
                before,
                False,
                lambda x: x['id']
            )
        }
    finally:
        db_session.close()
    return response