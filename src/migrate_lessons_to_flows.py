"""Migrate Lessons and Questions to ConversationFlows"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select, text

from src.database.models import (
    Lesson, Question, UserProgress,
    ConversationFlow, FlowBlock, FlowConnection, UserFlowState
)
from src.database.config import get_database_url


class LessonToFlowMigrator:
    """Migrate Lessons and Questions to ConversationFlow system"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.flow_map = {}  # lesson_id -> flow_id
        self.block_map = {}  # (lesson_id, block_type, index) -> block_id

    async def migrate_all(self):
        """Migrate all lessons to flows"""
        print("="*60)
        print(" LESSON TO FLOW MIGRATION")
        print("="*60)

        # Get all lessons ordered by order_number
        result = await self.session.execute(
            select(Lesson)
            .options(selectinload(Lesson.questions))
            .order_by(Lesson.order_number)
        )
        lessons = result.scalars().all()

        print(f"\nFound {len(lessons)} lessons to migrate\n")

        for lesson in lessons:
            await self.migrate_lesson(lesson)

        # Migrate user progress
        await self.migrate_user_progress()

        # Commit all changes
        await self.session.commit()

        print("\n" + "="*60)
        print(" MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        self.print_summary()

    async def migrate_lesson(self, lesson: Lesson):
        """Migrate a single lesson to a flow"""
        print(f"\n--- Migrating Lesson: {lesson.title} ---")
        print(f"  Order: {lesson.order_number}")
        print(f"  Questions: {len(lesson.questions)}")

        # Create flow
        flow = ConversationFlow(
            name=f"Lesson {lesson.order_number}: {lesson.title}",
            description=lesson.description,
            is_active=True,
            start_block_id=None  # Will be set after creating start block
        )
        self.session.add(flow)
        await self.session.flush()

        self.flow_map[lesson.id] = flow.id
        print(f"  Created flow: ID={flow.id}")

        # Calculate positions for visual layout
        x = 100
        y_start = 50
        y_step = 200

        # 1. Create Start block
        start_block = FlowBlock(
            flow_id=flow.id,
            block_type="start",
            label="Start",
            config={},
            position_x=x,
            position_y=y_start
        )
        self.session.add(start_block)
        await self.session.flush()
        flow.start_block_id = start_block.id
        self.block_map[(lesson.id, "start", 0)] = start_block.id
        y = y_start + y_step

        prev_block_id = start_block.id

        # 2. Create description text block (if description exists)
        if lesson.description:
            desc_block = FlowBlock(
                flow_id=flow.id,
                block_type="text",
                label="Description",
                config={
                    "text": lesson.description,
                    "parse_mode": "HTML"
                },
                position_x=x,
                position_y=y
            )
            self.session.add(desc_block)
            await self.session.flush()

            # Connect previous block to description
            await self.create_connection(
                flow.id, prev_block_id, desc_block.id, None
            )
            self.block_map[(lesson.id, "description", 0)] = desc_block.id
            prev_block_id = desc_block.id
            y += y_step
            print(f"  Created description block")

        # 3. Create video block
        if lesson.video_file_id:
            video_block = FlowBlock(
                flow_id=flow.id,
                block_type="video",
                label="Video Lesson",
                config={
                    "video_file_id": lesson.video_file_id,
                    "caption": f"Watch this video about {lesson.title}",
                    "protect_content": True
                },
                position_x=x,
                position_y=y
            )
            self.session.add(video_block)
            await self.session.flush()

            # Connect previous block to video
            await self.create_connection(
                flow.id, prev_block_id, video_block.id, None
            )
            self.block_map[(lesson.id, "video", 0)] = video_block.id
            prev_block_id = video_block.id
            y += y_step
            print(f"  Created video block")

        # 4. Create payment gate if not free
        if not lesson.is_free:
            payment_block = FlowBlock(
                flow_id=flow.id,
                block_type="payment_gate",
                label="Payment Check",
                config={
                    "required": True,
                    "unpaid_message": "This lesson requires payment. Use /pay to purchase access."
                },
                position_x=x,
                position_y=y
            )
            self.session.add(payment_block)
            await self.session.flush()

            # Connect previous block to payment
            await self.create_connection(
                flow.id, prev_block_id, payment_block.id, None
            )
            self.block_map[(lesson.id, "payment", 0)] = payment_block.id

            # Create unpaid message block
            unpaid_end_block = FlowBlock(
                flow_id=flow.id,
                block_type="end",
                label="End (Unpaid)",
                config={
                    "final_message": "Please complete payment to continue with this lesson."
                },
                position_x=x - 200,
                position_y=y + y_step
            )
            self.session.add(unpaid_end_block)
            await self.session.flush()

            # Connect payment to unpaid end
            await self.create_connection(
                flow.id, payment_block.id, unpaid_end_block.id, "unpaid"
            )
            self.block_map[(lesson.id, "end_unpaid", 0)] = unpaid_end_block.id

            prev_block_id = payment_block.id
            y += y_step
            print(f"  Created payment gate block")
        else:
            print(f"  Lesson is free - no payment gate")

        # 5. Create quiz blocks for each question
        quiz_count = len(lesson.questions)

        for i, question in enumerate(lesson.questions):
            quiz_block = FlowBlock(
                flow_id=flow.id,
                block_type="quiz",
                label=f"Question {i + 1}",
                config={
                    "question": question.text,
                    "options": question.options,
                    "correct_index": question.correct_option_index,
                    "explanation": None  # Could be added later
                },
                position_x=x,
                position_y=y
            )
            self.session.add(quiz_block)
            await self.session.flush()

            # Connect previous block to quiz
            await self.create_connection(
                flow.id, prev_block_id, quiz_block.id, None
            )
            self.block_map[(lesson.id, "quiz", i)] = quiz_block.id
            prev_block_id = quiz_block.id
            y += y_step

        print(f"  Created {quiz_count} quiz blocks")

        # 6. Create final end block
        end_block = FlowBlock(
            flow_id=flow.id,
            block_type="end",
            label="Complete",
            config={
                "final_message": f"Congratulations! You completed lesson {lesson.order_number}: {lesson.title}"
            },
            position_x=x,
            position_y=y
        )
        self.session.add(end_block)
        await self.session.flush()

        # Connect last quiz to end
        await self.create_connection(
            flow.id, prev_block_id, end_block.id, None
        )
        self.block_map[(lesson.id, "end", 0)] = end_block.id

        print(f"  Created end block")

    async def create_connection(
        self,
        flow_id: int,
        from_block_id: int,
        to_block_id: int,
        condition: str | None
    ):
        """Create a connection between two blocks"""
        connection = FlowConnection(
            flow_id=flow_id,
            from_block_id=from_block_id,
            to_block_id=to_block_id,
            condition=condition,
            condition_config={},
            connection_style={}
        )
        self.session.add(connection)
        await self.session.flush()

    async def migrate_user_progress(self):
        """Migrate UserProgress to UserFlowState"""
        print("\n" + "="*60)
        print(" MIGRATING USER PROGRESS")
        print("="*60)

        result = await self.session.execute(
            select(UserProgress)
        )
        progress_records = result.scalars().all()

        print(f"\nFound {len(progress_records)} user progress records\n")

        for progress in progress_records:
            # Check if lesson was migrated
            if progress.lesson_id not in self.flow_map:
                print(f"  [SKIP] No flow for lesson_id={progress.lesson_id}")
                continue

            flow_id = self.flow_map[progress.lesson_id]

            # Get the flow to find its end block
            flow_result = await self.session.execute(
                select(ConversationFlow).where(ConversationFlow.id == flow_id)
            )
            flow = flow_result.scalar_one_or_none()

            if not flow:
                print(f"  [SKIP] Flow not found: {flow_id}")
                continue

            # Create user flow state
            state = UserFlowState(
                user_id=progress.user_id,
                flow_id=flow_id,
                current_block_id=None if progress.passed else flow.start_block_id,
                context={
                    "attempts": progress.attempts,
                    "correct_answers": progress.correct_answers,
                    "total_questions": progress.total_questions,
                    "migrated_from_lesson": True,
                    "original_lesson_id": progress.lesson_id
                },
                is_completed=progress.passed,
                started_at=progress.completed_at,  # Approximation
                completed_at=progress.completed_at if progress.passed else None,
                last_activity=progress.completed_at
            )
            self.session.add(state)

            print(f"  Migrated: user_id={progress.user_id}, lesson={progress.lesson_id}, passed={progress.passed}")

        print(f"\nMigrated {len(progress_records)} user progress records")

    def print_summary(self):
        """Print migration summary"""
        print(f"\nFlows created: {len(self.flow_map)}")
        print(f"Lessons migrated: {list(self.flow_map.keys())}")


async def main():
    """Main migration function"""
    # Create async engine
    database_url = get_database_url()
    engine = create_async_engine(database_url, echo=False)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        migrator = LessonToFlowMigrator(session)

        try:
            await migrator.migrate_all()
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False

    await engine.dispose()
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
