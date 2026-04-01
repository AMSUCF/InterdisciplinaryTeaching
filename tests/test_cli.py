# tests/test_cli.py
from canvas_sync.__main__ import build_parser


def test_init_command():
    parser = build_parser()
    args = parser.parse_args(["init"])
    assert args.command == "init"


def test_push_all():
    parser = build_parser()
    args = parser.parse_args(["push", "--all"])
    assert args.command == "push"
    assert args.all is True
    assert args.week is None
    assert args.force is False


def test_push_week():
    parser = build_parser()
    args = parser.parse_args(["push", "--week", "3"])
    assert args.command == "push"
    assert args.week == 3
    assert args.all is False


def test_push_force():
    parser = build_parser()
    args = parser.parse_args(["push", "--week", "3", "--force"])
    assert args.force is True


def test_status_command():
    parser = build_parser()
    args = parser.parse_args(["status"])
    assert args.command == "status"


def test_diff_all():
    parser = build_parser()
    args = parser.parse_args(["diff", "--all"])
    assert args.command == "diff"
    assert args.all is True


def test_diff_week():
    parser = build_parser()
    args = parser.parse_args(["diff", "--week", "5"])
    assert args.command == "diff"
    assert args.week == 5
