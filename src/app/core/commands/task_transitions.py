from app.core.common.entities.types_ import TaskStatus

VALID_TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {TaskStatus.ASSIGNED, TaskStatus.CANCELLED},
    TaskStatus.ASSIGNED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.PHOTO_PROOF, TaskStatus.CANCELLED},
    TaskStatus.PHOTO_PROOF: {TaskStatus.COMPLETED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}
