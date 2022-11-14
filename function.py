from models import Note
from app import db
from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask_login import current_user

def create_note(text):
    note = Note(text=text, username_id = current_user.id)
    db.session.add(note)
    db.session.commit()
    db.session.refresh(note)


def read_notes():
    return db.session.query(Note).filter_by(username_id=current_user.id)


def update_note(note_id, text, done):
    db.session.query(Note).filter_by(id=note_id).update({
        "text": text,
        "done": True if done == "on" else False
    })
    db.session.commit()


def delete_note(text):
    print(text)
    db.session.query(Note).filter_by(text=text).delete()
    db.session.commit()
