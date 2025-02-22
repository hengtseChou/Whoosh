from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import URL, Email, InputRequired, Length, Optional, Regexp

SOCIAL_LINK_PLATFORM_CHOICES = [
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("twitter", "Twitter"),
    ("medium", "Medium"),
    ("linkedin", "LinkedIn"),
    ("github", "GitHub"),
]


class LoginForm(FlaskForm):
    """
    Form for user login. Inherits from FlaskForm.

    Fields:
        - email: StringField, required.
        - password: PasswordField, required.
        - persistent: BooleanField, optional.
        - submit_: SubmitField.
    """

    email = StringField(render_kw={"placeholder": "Email"}, validators=[InputRequired(), Email()])
    password = PasswordField(render_kw={"placeholder": "Password"}, validators=[InputRequired()])
    persistent = BooleanField("Keep me logged in")
    submit_ = SubmitField(label="Login")


class SignUpForm(FlaskForm):
    """
    Form for user sign-up. Inherits from FlaskForm.

    Fields:
        - email: StringField, required.
        - password: PasswordField, required.
        - username: StringField, required.
        - blogname: StringField, required.
        - terms: BooleanField, required.
        - submit_: SubmitField.
    """

    email = StringField(render_kw={"placeholder": "Email"}, validators=[InputRequired(), Email()])
    password = PasswordField(
        render_kw={"placeholder": "Password"},
        validators=[
            InputRequired(),
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="Password must be at least 8 characters long and include both upper and lower case letters and digits.",
            ),
        ],
    )
    username = StringField(
        render_kw={"placeholder": "Username"},
        validators=[
            InputRequired(),
            Regexp(
                "^(?![-.])[a-z0-9.-]*(?<![-.])$",
                message="Username can contains only lowercase letters, numbers, dashes, and dots, and does not start or end with a dash or dot.",
            ),
        ],
    )
    blogname = StringField(
        render_kw={"placeholder": "Blog's name"},
        validators=[
            InputRequired(),
            Length(min=1, max=20, message="Blog name must be between 1 and 20 characters."),
        ],
    )
    terms = BooleanField(
        "I understand this is a fully experimental project, and there is no guarantee of complete data preservation.",
        validators=[InputRequired()],
    )
    submit_ = SubmitField(label="Create")


class EditAboutForm(FlaskForm):
    """
    Form for editing user profile information. Inherits from FlaskForm.

    Fields:
        - profile_img_url: StringField, optional.
        - short_bio: StringField, optional.
        - editor: TextAreaField, optional. Connected to EasyMDE.
        - submit_: SubmitField.
    """

    profile_img_url = StringField(render_kw={"placeholder": "Insert image URL"})
    short_bio = StringField(render_kw={"placeholder": "Bio on your home page"})
    editor = TextAreaField(
        render_kw={
            "placeholder": "Note: If you want to include images in your post, you can upload them on [imgur.com](https://imgur.com)."
        }
    )
    submit_ = SubmitField(label="Save Changes")


class GeneralSettingsForm(FlaskForm):
    """
    Form for updating general settings. Inherits from FlaskForm.

    Fields:
        - cover_url: StringField, optional.
        - blogname: StringField, required.
        - gallery_enabled: BooleanField, optional.
        - changelog_enabled: BooleanField, optional.
        - submit_settings: SubmitField. The name is not submit_ is due to that we have several forms in this page.
    """

    cover_url = StringField(render_kw={"placeholder": "Insert image URL"})
    blogname = StringField(validators=[Length(min=1, max=20)])
    gallery_enabled = BooleanField()
    changelog_enabled = BooleanField()
    submit_settings = SubmitField(label="Save Changes")


class UpdateSocialLinksForm(FlaskForm):
    """
    Form for updating social media links. Inherits from FlaskForm.

    Fields:
        - url0, url1, url2, url3, url4: StringField, optional.
        - platform0, platform1, platform2, platform3, platform4: SelectField, optional.
        - submit_links: SubmitField. The name is not submit_ is due to that we have several forms in this page.
    """

    url0 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "https://..."})
    url1 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "https://..."})
    url2 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "https://..."})
    url3 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "https://..."})
    url4 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "https://..."})
    platform0 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform1 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform2 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform3 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform4 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    submit_links = SubmitField(label="Save Changes")


class UpdatePasswordForm(FlaskForm):
    """
    Form for updating user password. Inherits from FlaskForm.

    Fields:
        - current_pw: PasswordField, required.
        - new_pw: PasswordField, required.
        - new_pw_repeat: PasswordField, required.
        - submit_pw: SubmitField. The name is not submit_ is due to that we have several forms in this page.
    """

    current_pw = PasswordField()
    new_pw = PasswordField(
        validators=[
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="New password must be at least 8 characters long and include both upper and lower case letters and digits.",
            )
        ]
    )
    new_pw_repeat = PasswordField(
        validators=[
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="New password must be at least 8 characters long and include both upper and lower case letters and digits.",
            )
        ]
    )
    submit_pw = SubmitField(
        label="Save Changes", render_kw={"onclick": "return validateNewPassword()"}
    )


class UserDeletionForm(FlaskForm):
    """
    Form for deleting a user account. Inherits from FlaskForm.

    Fields:
        - password: PasswordField, required.
        - submit_delete: SubmitField. The name is not submit_ is due to that we have several forms in this page.
    """

    password = PasswordField(validators=[InputRequired()])
    submit_delete = SubmitField(label="Delete")
