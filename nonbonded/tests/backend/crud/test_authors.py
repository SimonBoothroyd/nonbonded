import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nonbonded.backend.database.crud.authors import AuthorCRUD
from nonbonded.tests.backend.crud.utilities import create_author


def test_simple_create_read(db: Session):

    author = create_author()

    db_author = AuthorCRUD.create(db, author)
    db.add(db_author)
    db.commit()

    retrieved_authors = AuthorCRUD.read_all(db)

    assert len(retrieved_authors) == 1

    retrieved_author = retrieved_authors[0]

    assert retrieved_author.name == author.name
    assert retrieved_author.email == author.email
    assert retrieved_author.institute == author.institute


def test_duplicate_separate_commits(db: Session):

    author = create_author()

    db_author = AuthorCRUD.create(db, author)
    db.add(db_author)
    db.commit()

    db_author = AuthorCRUD.create(db, author)
    db.add(db_author)
    db.commit()

    assert len(AuthorCRUD.read_all(db)) == 1


def test_duplicate_same_commit(db: Session):

    author = create_author()

    db_author = AuthorCRUD.create(db, author)
    db.add(db_author)

    db_author_2 = AuthorCRUD.create(db, author)
    db.add(db_author_2)

    db.commit()

    assert len(AuthorCRUD.read_all(db)) == 1


def test_fail_with_existing(db: Session):

    author = create_author()

    db_author = AuthorCRUD.create(db, author)
    db.add(db_author)
    db.commit()

    author_2 = create_author()
    author_2.name += " 2"

    db_author_2 = AuthorCRUD.create(db, author_2)
    db.add(db_author_2)

    with pytest.raises(IntegrityError):
        db.commit()
