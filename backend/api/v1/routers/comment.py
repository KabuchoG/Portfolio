#!/usr/bin/python3
from datetime import datetime
from operator import and_
import uuid
from fastapi import APIRouter

from ..form_types import CommentAddForm, CommentDeleteForm
from ..database import get_session, User, Comment
from ..utils.token_handlers import AuthToken
from ..utils.pagination import extract_page


router = APIRouter(prefix='/api/v1')


@router.get('/poem-comments')
async def get_poem_comments(
    id='',
    span=12,
    after='',
    before=''
    ):
    response = {
        'success': False,
        'message': 'Failed to find comments.'
    }
    if span < 0:
        span = -span
    db_session = get_session()
    try:
        result = db_session.query(
            Comment).filter(and_(
                Comment.poem_id == id,
                Comment.comment_id == None
            )).all()
        new_result = []
        if result is not None:
            for item in result:
                user = db_session.query(
                    User).filter(User.id == item.user_id).first()
                if not user:
                    continue
                replies = db_session.query(
                    Comment).filter(
                        and_(
                            Comment.poem_id == id,
                            Comment.comment_id == item.id,
                    )).all()
                replies_count = len(replies) if replies else 0
                obj = {
                    'id': item.id,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'profilePhotoId': user.profile_photo_id
                    },
                    'createdOn': item.created_on.isoformat(),
                    'text': item.text,
                    'poemId': item.poem_id,
                    'repliesCount': replies_count
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


@router.get('/comment-replies')
async def get_comment_replies(
    id='',
    poemId='',
    span=12,
    after='',
    before=''
    ):
    response = {
        'success': False,
        'message': 'Failed to find replies to comment.'
    }
    if span < 0:
        span = -span
    if not id or not poemId:
        return response
    db_session = get_session()
    try:
        result = db_session.query(
            Comment).filter(and_(
                Comment.poem_id == poemId,
                Comment.comment_id == id
            )).all()
        new_result = []
        if result is not None:
            for item in result:
                user = db_session.query(
                    User).filter(User.id == item.user_id).first()
                if not user:
                    continue
                obj = {
                    'id': item.id,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'profilePhotoId': user.profile_photo_id
                    },
                    'createdOn': item.created_on.isoformat(),
                    'text': item.text,
                    'poemId': poemId,
                    'replyTo': id
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


@router.get('/user-comments')
async def get_user_comments(
    token='',
    span=12,
    after='',
    before=''
    ):
    response = {
        'success': False,
        'message': 'Failed to find comments.'
    }
    auth_token = AuthToken.decode(token)
    if span < 0:
        span = -span
    db_session = get_session()
    try:
        result = db_session.query(
            Comment).filter(
                Comment.user_id == auth_token.user_id).all()
        user = db_session.query(
            User).filter(User.id == auth_token.user_id).first()
        if not user:
            return response
        new_result = []
        if result is not None:
            for item in result:
                replies = db_session.query(
                    Comment).filter(
                        Comment.comment_id == item.id).all()
                replies_count = len(replies) if replies else 0
                obj = {
                    'id': item.id,
                    'createdOn': item.created_on.isoformat(),
                    'text': item.text,
                    'poemId': item.poem_id,
                    'replyTo': item.comment_id if item.comment_id else '',
                    'repliesCount': replies_count
                }
                new_result.append(obj)
        response = {
            'success': True,
            'data': {
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'profilePhotoId': user.profile_photo_id
                },
                'comments': extract_page(
                    new_result,
                    span,
                    after,
                    before,
                    False,
                    lambda x: x['id']
                )
            }
        }
    finally:
        db_session.close()
    return response


@router.post('/poem-comments')
async def add_comment(body: CommentAddForm):
    response = {
        'success': False,
        'message': 'Failed to add comment.'
    }
    auth_token = AuthToken.decode(body.authToken)
    wrong_conditions = [
        auth_token is None,
        auth_token is not None and (auth_token.user_id != body.userId),
        len(body.text) > 400
    ]
    if any(wrong_conditions):
        return response
    db_session = get_session()
    try:
        if body.replyTo:
            result = db_session.query(
                Comment).filter(
                    and_(
                        Comment.poem_id == body.poemId,
                        Comment.comment_id == None
                )).first()
            if not result:
                db_session.close()
                return response
        gen_id = str(uuid.uuid4())
        cur_time = datetime.utcnow()
        comment = Comment(
            id=gen_id,
            created_on=cur_time,
            poem_id=body.poemId,
            user_id=body.userId,
            comment_id=body.replyTo,
            text=body.text,
        )
        db_session.add(comment)
        db_session.commit()
        response = {
            'success': True,
            'data': {
                'id': gen_id,
                'createdOn': cur_time.isoformat(),
                'replyTo': body.replyTo if body.replyTo else '',
                'poemId': body.poemId,
                'repliesCount': 0
            }
        }
    except Exception as ex:
        print(ex.args[0])
        db_session.rollback()
    finally:
        db_session.close()
    return response


@router.delete('/poem-comments')
async def remove_user(body: CommentDeleteForm):
    response = {
        'success': False,
        'message': 'Failed to remove comment.'
    }
    auth_token = AuthToken.decode(body.authToken)
    if auth_token is None or auth_token.user_id != body.userId:
        return response
    db_session = get_session()
    try:
        db_session.query(Comment).filter(and_(
                Comment.poem_id == body.poemId,
                Comment.comment_id == body.commentId,
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