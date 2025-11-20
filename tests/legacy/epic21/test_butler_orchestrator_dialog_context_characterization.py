"""Characterization tests for ButlerOrchestrator dialog context behavior.

These tests capture the current behavior of dialog context persistence
BEFORE any refactoring. They ensure we don't break existing functionality.

Epic 21 · Stage 21_01a · Dialog Context Repository
"""

import pytest

from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.agents.handlers.chat_handler import ChatHandler
from src.domain.agents.handlers.data_handler import DataHandler
from src.domain.agents.handlers.homework_handler import HomeworkHandler
from src.domain.agents.handlers.task_handler import TaskHandler
from src.domain.agents.services.mode_classifier import DialogMode, ModeClassifier
from src.domain.agents.state_machine import DialogContext, DialogState


@pytest.mark.characterization
@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.dialog_context
@pytest.mark.integration
@pytest.mark.requires_mongo
@pytest.mark.asyncio
class TestButlerOrchestratorDialogContextCharacterization:
    """Characterization tests for dialog context persistence.

    These tests capture how ButlerOrchestrator currently works with MongoDB
    for dialog context storage. DO NOT modify these tests during refactoring -
    they serve as regression protection.
    """

    async def test_context_creation_for_new_session(
        self, butler_mock_mongodb, sample_handlers
    ):
        """Characterization: New session creates empty context.

        Captures current behavior: when a session doesn't exist,
        a new context is created with IDLE state.
        """

        # Create a mock dialog context repository that uses the mock mongodb
        class MockDialogContextRepository:
            def __init__(self, mongodb):
                self.collection = mongodb.dialog_contexts

            async def get_by_session(self, session_id: str):
                from src.domain.agents.state_machine import DialogContext, DialogState

                doc = await self.collection.find_one({"session_id": session_id})
                if doc:
                    return DialogContext(
                        state=DialogState(doc["state"]),
                        user_id=doc["user_id"],
                        session_id=doc["session_id"],
                        data=doc.get("data", {}),
                        step_count=doc.get("step_count", 0),
                    )
                return None

            async def save(self, context):
                doc = {
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "state": context.state.value,
                    "data": context.data,
                    "step_count": context.step_count,
                }
                await self.collection.update_one(
                    {"session_id": context.session_id},
                    {"$set": doc},
                    upsert=True,
                )

            async def delete(self, session_id: str):
                await self.collection.delete_one({"session_id": session_id})

        mock_repo = MockDialogContextRepository(butler_mock_mongodb)
        orchestrator = ButlerOrchestrator(
            mode_classifier=sample_handlers["mode_classifier"],
            task_handler=sample_handlers["task_handler"],
            data_handler=sample_handlers["data_handler"],
            homework_handler=sample_handlers["homework_handler"],
            chat_handler=sample_handlers["chat_handler"],
            dialog_context_repository=mock_repo,
        )

        # Act: Get context for non-existent session
        context = await orchestrator._get_or_create_context(
            user_id="alice", session_id="new_session_123"
        )

        # Assert: New context created with expected defaults
        assert context.user_id == "alice"
        assert context.session_id == "new_session_123"
        assert context.state == DialogState.IDLE
        assert context.data == {}
        assert context.step_count == 0

    async def test_context_loading_from_existing_document(
        self, butler_mock_mongodb, sample_handlers
    ):
        """Characterization: Existing session loads from MongoDB.

        Captures current behavior: when a session exists in DB,
        its context is loaded and deserialized correctly.
        """

        # Create a mock dialog context repository that uses the mock mongodb
        class MockDialogContextRepository:
            def __init__(self, mongodb):
                self.collection = mongodb.dialog_contexts

            async def get_by_session(self, session_id: str):
                from src.domain.agents.state_machine import DialogContext, DialogState

                doc = await self.collection.find_one({"session_id": session_id})
                if doc:
                    return DialogContext(
                        state=DialogState(doc["state"]),
                        user_id=doc["user_id"],
                        session_id=doc["session_id"],
                        data=doc.get("data", {}),
                        step_count=doc.get("step_count", 0),
                    )
                return None

            async def save(self, context):
                doc = {
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "state": context.state.value,
                    "data": context.data,
                    "step_count": context.step_count,
                }
                await self.collection.update_one(
                    {"session_id": context.session_id},
                    {"$set": doc},
                    upsert=True,
                )

            async def delete(self, session_id: str):
                await self.collection.delete_one({"session_id": session_id})

        mock_repo = MockDialogContextRepository(butler_mock_mongodb)
        orchestrator = ButlerOrchestrator(
            mode_classifier=sample_handlers["mode_classifier"],
            task_handler=sample_handlers["task_handler"],
            data_handler=sample_handlers["data_handler"],
            homework_handler=sample_handlers["homework_handler"],
            chat_handler=sample_handlers["chat_handler"],
            dialog_context_repository=mock_repo,
        )

        # Arrange: Create document in MongoDB (simulating existing session)
        existing_doc = {
            "session_id": "existing_session_456",
            "user_id": "bob",
            "state": "task_create_title",  # DialogState.TASK_CREATE_TITLE.value
            "data": {"task_title": "Buy milk"},
            "step_count": 2,
        }
        await butler_mock_mongodb.dialog_contexts.insert_one(existing_doc)

        # Act: Get context for existing session
        context = await orchestrator._get_or_create_context(
            user_id="bob", session_id="existing_session_456"
        )

        # Assert: Context loaded from DB with correct values
        assert context.user_id == "bob"
        assert context.session_id == "existing_session_456"
        assert context.state == DialogState.TASK_CREATE_TITLE
        assert context.data == {"task_title": "Buy milk"}
        assert context.step_count == 2

    async def test_context_saving_updates_mongodb_document(
        self, butler_mock_mongodb, sample_handlers
    ):
        """Characterization: Context saving updates MongoDB.

        Captures current behavior: saving a context creates/updates
        the MongoDB document with serialized data.
        """

        # Create a mock dialog context repository that uses the mock mongodb
        class MockDialogContextRepository:
            def __init__(self, mongodb):
                self.collection = mongodb.dialog_contexts

            async def get_by_session(self, session_id: str):
                from src.domain.agents.state_machine import DialogContext, DialogState

                doc = await self.collection.find_one({"session_id": session_id})
                if doc:
                    return DialogContext(
                        state=DialogState(doc["state"]),
                        user_id=doc["user_id"],
                        session_id=doc["session_id"],
                        data=doc.get("data", {}),
                        step_count=doc.get("step_count", 0),
                    )
                return None

            async def save(self, context):
                doc = {
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "state": context.state.value,
                    "data": context.data,
                    "step_count": context.step_count,
                }
                await self.collection.update_one(
                    {"session_id": context.session_id},
                    {"$set": doc},
                    upsert=True,
                )

            async def delete(self, session_id: str):
                await self.collection.delete_one({"session_id": session_id})

        mock_repo = MockDialogContextRepository(butler_mock_mongodb)
        orchestrator = ButlerOrchestrator(
            mode_classifier=sample_handlers["mode_classifier"],
            task_handler=sample_handlers["task_handler"],
            data_handler=sample_handlers["data_handler"],
            homework_handler=sample_handlers["homework_handler"],
            chat_handler=sample_handlers["chat_handler"],
            dialog_context_repository=mock_repo,
        )

        # Arrange: Create context to save
        context = DialogContext(
            state=DialogState.DATA_COLLECTING,
            user_id="charlie",
            session_id="save_test_789",
            data={"query": "population of Tokyo"},
            step_count=1,
        )

        # Act: Save context
        await orchestrator._save_context(context)

        # Assert: Document exists in MongoDB with correct data
        doc = await butler_mock_mongodb.dialog_contexts.find_one(
            {"session_id": "save_test_789"}
        )
        assert doc is not None
        assert doc["user_id"] == "charlie"
        assert doc["session_id"] == "save_test_789"
        assert doc["state"] == "data_collecting"  # DialogState.DATA_COLLECTING.value
        assert doc["data"] == {"query": "population of Tokyo"}
        assert doc["step_count"] == 1

    async def test_context_update_overwrites_existing_document(
        self, butler_mock_mongodb, sample_handlers
    ):
        """Characterization: Context updates overwrite existing data.

        Captures current behavior: saving updated context replaces
        the existing MongoDB document entirely.
        """

        # Create a mock dialog context repository that uses the mock mongodb
        class MockDialogContextRepository:
            def __init__(self, mongodb):
                self.collection = mongodb.dialog_contexts

            async def get_by_session(self, session_id: str):
                from src.domain.agents.state_machine import DialogContext, DialogState

                doc = await self.collection.find_one({"session_id": session_id})
                if doc:
                    return DialogContext(
                        state=DialogState(doc["state"]),
                        user_id=doc["user_id"],
                        session_id=doc["session_id"],
                        data=doc.get("data", {}),
                        step_count=doc.get("step_count", 0),
                    )
                return None

            async def save(self, context):
                doc = {
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "state": context.state.value,
                    "data": context.data,
                    "step_count": context.step_count,
                }
                await self.collection.update_one(
                    {"session_id": context.session_id},
                    {"$set": doc},
                    upsert=True,
                )

            async def delete(self, session_id: str):
                await self.collection.delete_one({"session_id": session_id})

        mock_repo = MockDialogContextRepository(butler_mock_mongodb)
        orchestrator = ButlerOrchestrator(
            mode_classifier=sample_handlers["mode_classifier"],
            task_handler=sample_handlers["task_handler"],
            data_handler=sample_handlers["data_handler"],
            homework_handler=sample_handlers["homework_handler"],
            chat_handler=sample_handlers["chat_handler"],
            dialog_context_repository=mock_repo,
        )

        # Arrange: Save initial context
        initial_context = DialogContext(
            state=DialogState.IDLE,
            user_id="diana",
            session_id="update_test_999",
            data={},
            step_count=0,
        )
        await orchestrator._save_context(initial_context)

        # Verify initial save
        doc = await butler_mock_mongodb.dialog_contexts.find_one(
            {"session_id": "update_test_999"}
        )
        assert doc["state"] == "idle"
        assert doc["step_count"] == 0

        # Act: Update and save modified context
        updated_context = DialogContext(
            state=DialogState.TASK_CREATE_TITLE,
            user_id="diana",
            session_id="update_test_999",
            data={"task": "Write code"},
            step_count=3,
        )
        await orchestrator._save_context(updated_context)

        # Assert: Document updated with new values
        updated_doc = await butler_mock_mongodb.dialog_contexts.find_one(
            {"session_id": "update_test_999"}
        )
        assert updated_doc["state"] == "task_create_title"
        assert updated_doc["data"] == {"task": "Write code"}
        assert updated_doc["step_count"] == 3

        # Verify only one document exists (not duplicated)
        count = await butler_mock_mongodb.dialog_contexts.count_documents(
            {"session_id": "update_test_999"}
        )
        assert count == 1

    async def test_full_message_handling_cycle_preserves_context(
        self, butler_mock_mongodb, sample_handlers
    ):
        """Characterization: Full message handling preserves context.

        Captures current behavior: complete message handling cycle
        (load → process → save) maintains context integrity.
        """

        # Create a mock dialog context repository that uses the mock mongodb
        class MockDialogContextRepository:
            def __init__(self, mongodb):
                self.collection = mongodb.dialog_contexts

            async def get_by_session(self, session_id: str):
                from src.domain.agents.state_machine import DialogContext, DialogState

                doc = await self.collection.find_one({"session_id": session_id})
                if doc:
                    return DialogContext(
                        state=DialogState(doc["state"]),
                        user_id=doc["user_id"],
                        session_id=doc["session_id"],
                        data=doc.get("data", {}),
                        step_count=doc.get("step_count", 0),
                    )
                return None

            async def save(self, context):
                doc = {
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "state": context.state.value,
                    "data": context.data,
                    "step_count": context.step_count,
                }
                await self.collection.update_one(
                    {"session_id": context.session_id},
                    {"$set": doc},
                    upsert=True,
                )

            async def delete(self, session_id: str):
                await self.collection.delete_one({"session_id": session_id})

        mock_repo = MockDialogContextRepository(butler_mock_mongodb)
        orchestrator = ButlerOrchestrator(
            mode_classifier=sample_handlers["mode_classifier"],
            task_handler=sample_handlers["task_handler"],
            data_handler=sample_handlers["data_handler"],
            homework_handler=sample_handlers["homework_handler"],
            chat_handler=sample_handlers["chat_handler"],
            dialog_context_repository=mock_repo,
        )

        # Mock mode classifier to return IDLE (chat mode)
        sample_handlers["mode_classifier"].classify.return_value = DialogMode.IDLE

        # Mock chat handler response
        sample_handlers["chat_handler"].handle.return_value = "Hello! How can I help?"

        # Act: Handle first message (creates context)
        response1 = await orchestrator.handle_user_message(
            user_id="eve", message="Hi there", session_id="cycle_test_111"
        )

        # Verify response and context creation
        assert "Hello! How can I help?" in response1

        # Verify context was saved
        doc1 = await butler_mock_mongodb.dialog_contexts.find_one(
            {"session_id": "cycle_test_111"}
        )
        assert doc1["user_id"] == "eve"
        assert doc1["state"] == "idle"

        # Act: Handle second message (loads existing context)
        sample_handlers["chat_handler"].handle.return_value = (
            "I remember you from before!"
        )
        response2 = await orchestrator.handle_user_message(
            user_id="eve", message="How are you?", session_id="cycle_test_111"
        )

        # Verify response and context preservation
        assert "I remember you from before!" in response2

        # Verify context still exists and unchanged
        doc2 = await butler_mock_mongodb.dialog_contexts.find_one(
            {"session_id": "cycle_test_111"}
        )
        assert doc2["user_id"] == "eve"
        assert doc2["state"] == "idle"
        assert doc2["session_id"] == "cycle_test_111"

    async def test_context_serialization_format(
        self, butler_mock_mongodb, sample_handlers
    ):
        """Characterization: Context serialization format.

        Captures current behavior: how DialogContext is converted
        to MongoDB document format.
        """

        # Create a mock dialog context repository that uses the mock mongodb
        class MockDialogContextRepository:
            def __init__(self, mongodb):
                self.collection = mongodb.dialog_contexts

            async def get_by_session(self, session_id: str):
                from src.domain.agents.state_machine import DialogContext, DialogState

                doc = await self.collection.find_one({"session_id": session_id})
                if doc:
                    return DialogContext(
                        state=DialogState(doc["state"]),
                        user_id=doc["user_id"],
                        session_id=doc["session_id"],
                        data=doc.get("data", {}),
                        step_count=doc.get("step_count", 0),
                    )
                return None

            async def save(self, context):
                doc = {
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "state": context.state.value,
                    "data": context.data,
                    "step_count": context.step_count,
                }
                await self.collection.update_one(
                    {"session_id": context.session_id},
                    {"$set": doc},
                    upsert=True,
                )

            async def delete(self, session_id: str):
                await self.collection.delete_one({"session_id": session_id})

        mock_repo = MockDialogContextRepository(butler_mock_mongodb)
        orchestrator = ButlerOrchestrator(
            mode_classifier=sample_handlers["mode_classifier"],
            task_handler=sample_handlers["task_handler"],
            data_handler=sample_handlers["data_handler"],
            homework_handler=sample_handlers["homework_handler"],
            chat_handler=sample_handlers["chat_handler"],
            dialog_context_repository=mock_repo,
        )

        # Test serialization directly
        context = DialogContext(
            state=DialogState.DATA_COLLECTING,
            user_id="frank",
            session_id="serialization_test",
            data={"assignment_id": "hw123", "files": ["main.py"]},
            step_count=5,
        )

        serialized = orchestrator._serialize_context(context)

        # Verify exact format expected by current code
        expected = {
            "user_id": "frank",
            "session_id": "serialization_test",
            "state": "data_collecting",  # Enum value
            "data": {"assignment_id": "hw123", "files": ["main.py"]},
            "step_count": 5,
        }
        assert serialized == expected

    async def test_context_deserialization_from_mongodb_format(
        self, butler_mock_mongodb, sample_handlers
    ):
        """Characterization: Context deserialization from MongoDB.

        Captures current behavior: how MongoDB document is converted
        back to DialogContext object.
        """

        # Create a mock dialog context repository that uses the mock mongodb
        class MockDialogContextRepository:
            def __init__(self, mongodb):
                self.collection = mongodb.dialog_contexts

            async def get_by_session(self, session_id: str):
                from src.domain.agents.state_machine import DialogContext, DialogState

                doc = await self.collection.find_one({"session_id": session_id})
                if doc:
                    return DialogContext(
                        state=DialogState(doc["state"]),
                        user_id=doc["user_id"],
                        session_id=doc["session_id"],
                        data=doc.get("data", {}),
                        step_count=doc.get("step_count", 0),
                    )
                return None

            async def save(self, context):
                doc = {
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "state": context.state.value,
                    "data": context.data,
                    "step_count": context.step_count,
                }
                await self.collection.update_one(
                    {"session_id": context.session_id},
                    {"$set": doc},
                    upsert=True,
                )

            async def delete(self, session_id: str):
                await self.collection.delete_one({"session_id": session_id})

        mock_repo = MockDialogContextRepository(butler_mock_mongodb)
        orchestrator = ButlerOrchestrator(
            mode_classifier=sample_handlers["mode_classifier"],
            task_handler=sample_handlers["task_handler"],
            data_handler=sample_handlers["data_handler"],
            homework_handler=sample_handlers["homework_handler"],
            chat_handler=sample_handlers["chat_handler"],
            dialog_context_repository=mock_repo,
        )

        # Simulate MongoDB document format
        mongodb_doc = {
            "session_id": "deserialization_test",
            "user_id": "grace",
            "state": "data_collecting",
            "data": {"search_query": "weather in Paris"},
            "step_count": 1,
            # Note: MongoDB might add _id field, but our code ignores it
        }

        # Test deserialization directly
        context = orchestrator._deserialize_context(mongodb_doc)

        # Verify exact object created
        assert isinstance(context, DialogContext)
        assert context.user_id == "grace"
        assert context.session_id == "deserialization_test"
        assert context.state == DialogState.DATA_COLLECTING
        assert context.data == {"search_query": "weather in Paris"}
        assert context.step_count == 1

    async def test_missing_fields_in_mongodb_document_use_defaults(
        self, butler_mock_mongodb, sample_handlers
    ):
        """Characterization: Missing fields in MongoDB use defaults.

        Captures current behavior: when MongoDB document lacks
        optional fields, deserialization uses sensible defaults.
        """

        # Create a mock dialog context repository that uses the mock mongodb
        class MockDialogContextRepository:
            def __init__(self, mongodb):
                self.collection = mongodb.dialog_contexts

            async def get_by_session(self, session_id: str):
                from src.domain.agents.state_machine import DialogContext, DialogState

                doc = await self.collection.find_one({"session_id": session_id})
                if doc:
                    return DialogContext(
                        state=DialogState(doc["state"]),
                        user_id=doc["user_id"],
                        session_id=doc["session_id"],
                        data=doc.get("data", {}),
                        step_count=doc.get("step_count", 0),
                    )
                return None

            async def save(self, context):
                doc = {
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "state": context.state.value,
                    "data": context.data,
                    "step_count": context.step_count,
                }
                await self.collection.update_one(
                    {"session_id": context.session_id},
                    {"$set": doc},
                    upsert=True,
                )

            async def delete(self, session_id: str):
                await self.collection.delete_one({"session_id": session_id})

        mock_repo = MockDialogContextRepository(butler_mock_mongodb)
        orchestrator = ButlerOrchestrator(
            mode_classifier=sample_handlers["mode_classifier"],
            task_handler=sample_handlers["task_handler"],
            data_handler=sample_handlers["data_handler"],
            homework_handler=sample_handlers["homework_handler"],
            chat_handler=sample_handlers["chat_handler"],
            dialog_context_repository=mock_repo,
        )

        # Document with minimal required fields only
        minimal_doc = {
            "session_id": "minimal_test",
            "user_id": "henry",
            "state": "idle",
            # Missing: data, step_count
        }

        context = orchestrator._deserialize_context(minimal_doc)

        # Verify defaults applied
        assert context.data == {}  # Default empty dict
        assert context.step_count == 0  # Default zero
