from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"],default="bcrypt", deprecated="auto")

class Hash:
    @staticmethod
    def bcrypt(password: str) -> str:
        if not isinstance(password, str):
            raise TypeError(f"Password must be str, got {type(password)}")
        plen = len(password.encode("utf-8"))
        if plen > 72:
            # Optional: hash a truncated version OR raise early with clarity
            raise ValueError(f"Password UTF-8 length {plen} > 72: value startswith={password[:20]!r}")
        return pwd_context.hash(password)
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)