"""
seed.py — populate the database with realistic fake data using Faker.
Run with:  python seed.py
"""

from faker import Faker
from app import create_app, db
from models import User, JournalEntry

fake = Faker()

MOODS = ["happy", "sad", "anxious", "grateful", "angry", "calm", "excited", "tired"]


def seed_users(n=5):
    """Create n fake users with hashed passwords."""
    users = []
    for _ in range(n):
        user = User(
            username=fake.unique.user_name(),
            email=fake.unique.email(),
        )
        # password = "password123" for every seed user — easy to test with
        user.password = "password123"
        db.session.add(user)
        users.append(user)
    db.session.commit()
    print(f"  ✓ Created {n} users")
    return users


def seed_entries(users, entries_per_user=8):
    """Create journal entries distributed across all seeded users."""
    total = 0
    for user in users:
        for _ in range(entries_per_user):
            entry = JournalEntry(
                title      = fake.sentence(nb_words=6).rstrip("."),
                content    = fake.paragraph(nb_sentences=5),
                mood       = fake.random_element(MOODS),
                is_private = fake.boolean(chance_of_getting_true=70),
                user_id    = user.id,
            )
            db.session.add(entry)
            total += 1
    db.session.commit()
    print(f"  ✓ Created {total} journal entries")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("Dropping existing tables...")
        db.drop_all()
        print("Creating tables...")
        db.create_all()
        print("Seeding...")
        users = seed_users(n=5)
        seed_entries(users, entries_per_user=8)
        print("Done! Seed usernames use password: password123")