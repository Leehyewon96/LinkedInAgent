# APScheduler

# scheduler.py
import sys
import logging
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.append(str(Path(__file__).parent / "graph"))
sys.path.append(str(Path(__file__).parent / "agents"))

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/scheduler.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def on_job_executed(event):
    logger.info(f"성공 | job={event.job_id}")

def on_job_error(event):
    logger.error(f"실패 | job={event.job_id} | {event.exception}")


def run_pipeline():
    from pipeline import build_graph
    logger.info("파이프라인 시작")
    app = build_graph()
    app.invoke({})
    logger.info("파이프라인 완료")


def create_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone="Asia/Seoul")
    scheduler.add_listener(on_job_executed, EVENT_JOB_EXECUTED)
    scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)
    scheduler.add_job(
        run_pipeline,
        trigger=CronTrigger(hour=9, minute=0),
        id="linkedin_daily",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=1800,
    )
    return scheduler


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", action="store_true", help="즉시 실행")
    args = parser.parse_args()

    if args.now:
        run_pipeline()
    else:
        # logs 폴더 없으면 생성
        Path("logs").mkdir(exist_ok=True)
        scheduler = create_scheduler()
        logger.info("스케줄러 시작 | 매일 09:00 KST 자동 실행")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("스케줄러 종료")