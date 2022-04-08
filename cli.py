from ssg.generate_site import generate_site
from ssg.settings import settings


def main() -> None:
    generate_site(settings)


if __name__ == "__main__":
    main()
