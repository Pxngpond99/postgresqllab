import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://coe:CoEpasswd@localhost:5432/coedb"
)

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"], defaults={"note_id": None})
@app.route("/notes/<note_id>/edit", methods=["GET", "POST"])
def notes_create_edit(note_id):
    form = forms.NoteForm()
    db = models.db
    note = None
    if note_id:
        note = (
            db.session.execute(db.select(models.Note).where(models.Note.id == note_id))
            .scalars()
            .first()
        )

    if not form.validate_on_submit():
        if note:
            form.title.data = note.title
            form.description.data = note.description
            form.tags.data = [",".join([i.name for i in note.tags])]
        print("error", form.errors)
        return flask.render_template(
            "notes-create-edit.html",
            form=form,
        )
    if not note_id:
        note = models.Note()
        form.populate_obj(note)
    else:
        note.title = form.title.data
        note.description = form.description.data

    note.tags = []

    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)
        note.tags.append(tag)

    other_tag_name = [
        i.name
        for i in db.session.execute(db.select(models.Tag)).scalars()
        if i.name not in form.tags.data
    ]
    for tag_name in other_tag_name:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )
        notes = (
            db.session.execute(
                db.select(models.Note).where(models.Note.tags.any(id=tag.id))
            )
            .scalars()
            .first()
        )
        if not notes:
            db.session.delete(tag)

    if not note_id:
        db.session.add(note)

    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/notes/<note_id>/delete", methods=["GET", "POST"])
def notes_delete(note_id):
    db = models.db
    note = (
        db.session.execute(db.select(models.Note).where(models.Note.id == note_id))
        .scalars()
        .first()
    )

    for tag_name in note.tags:
        tag = (
            db.session.execute(
                db.select(models.Tag).where(models.Tag.name == tag_name.name)
            )
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)

            notes = (
                db.session.execute(
                    db.select(models.Note).where(models.Note.tags.any(id=tag.id))
                )
                .scalars()
                .first()
            )
            if not notes:
                db.session.delete(tag)

    db.session.delete(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/all")
def tags():
    db = models.db
    tags = db.session.execute(db.select(models.Tag).order_by(models.Tag.name)).scalars()
    return flask.render_template(
        "tags-all.html",
        tags=tags,
    )


@app.route("/tags/<tag_name>/edit", methods=["GET", "POST"])
def tags_edit(tag_name):
    db = models.db
    forms
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    form = forms.TagForm()
    if not form.validate_on_submit():
        form.name.data = tag.name
        print(f"error {form.errors}")
        return flask.render_template("tags-edit.html", form=form)
    tag.name = form.name.data
    db.session.commit()
    return flask.redirect(flask.url_for("tags"))


@app.route("/tags/<tag_name>/delete", methods=["GET", "POST"])
def tags_delete(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()
    for note in notes:
        new_tag = [tag_n for tag_n in note.tags if tag_n != tag]
        note.tags = new_tag

    db.session.delete(tag)
    db.session.commit()

    return flask.redirect(flask.url_for("tags"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


if __name__ == "__main__":
    app.run(debug=True)
