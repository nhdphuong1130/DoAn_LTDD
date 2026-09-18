from english7.api.errors import ApplicationError
from english7.core.security import PasswordHasher, TokenService
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.repository import AuthRepository


class AuthService:
    def __init__(
        self,
        repository: AuthRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self.repository = repository
        self.password_hasher = password_hasher
        self.token_service = token_service

    def register(self, email: str, password: str) -> AuthUser:
        normalized_email = email.strip().lower()
        if self.repository.get_by_email(normalized_email) is not None:
            raise ApplicationError(
                code="email_already_registered",
                message="Email is already registered",
                status_code=409,
            )
        user = AuthUser.new(
            email=normalized_email,
            password_hash=self.password_hasher.hash(password),
        )
        return self.repository.create(user)

    def login(self, email: str, password: str) -> str:
        user = self.repository.get_by_email(email.strip().lower())
        if (
            user is None
            or not user.is_active
            or not self.password_hasher.verify(password, user.password_hash)
        ):
            raise ApplicationError(
                code="invalid_credentials",
                message="Email or password is incorrect",
                status_code=401,
            )
        return self.token_service.issue(user)

    def authenticate_token(self, encoded: str) -> AuthUser:
        claims = self.token_service.decode(encoded)
        user = self.repository.get_by_id(claims.subject)
        if user is None or not user.is_active:
            raise ApplicationError(
                code="invalid_token",
                message="Access token is invalid",
                status_code=401,
            )
        return user

    @staticmethod
    def authorize(user: AuthUser, allowed_roles: set[str]) -> AuthUser:
        if user.role not in allowed_roles:
            raise ApplicationError(
                code="forbidden",
                message="You do not have permission to perform this action",
                status_code=403,
            )
        return user

