from collections import Counter
import hashlib

from .models import LeetCodeProblem, ProblemCompletion


class PersonalizedExerciseService:
    """Build personalized practice recommendations from user history."""

    DEFAULT_COUNT = 10
    MAX_COUNT = 30
    VALID_STRATEGIES = {"balanced", "review", "challenge"}
    VALID_DIFFICULTIES = {"easy", "medium", "hard"}
    _DIFFICULTY_LEVEL = {"easy": 0, "medium": 1, "hard": 2}
    _LEVEL_TO_DIFFICULTY = {0: "easy", 1: "medium", 2: "hard"}

    _STRATEGY_WEIGHTS = {
        "balanced": {
            "retry": 46,
            "weak_tag": 10,
            "difficulty_exact": 18,
            "difficulty_near": 9,
            "novelty": 3,
        },
        "review": {
            "retry": 68,
            "weak_tag": 14,
            "difficulty_exact": 12,
            "difficulty_near": 6,
            "novelty": 1,
        },
        "challenge": {
            "retry": 24,
            "weak_tag": 8,
            "difficulty_exact": 22,
            "difficulty_near": 11,
            "novelty": 5,
        },
    }

    @classmethod
    def generate_for_user(
        cls,
        user,
        *,
        count=DEFAULT_COUNT,
        strategy="balanced",
        difficulty=None,
        focus_tag=None,
        include_completed=False,
    ):
        count = max(1, min(int(count or cls.DEFAULT_COUNT), cls.MAX_COUNT))
        strategy = strategy if strategy in cls.VALID_STRATEGIES else "balanced"
        difficulty = difficulty if difficulty in cls.VALID_DIFFICULTIES else None
        normalized_focus_tag = cls._normalize_tag(focus_tag)

        completions = list(
            ProblemCompletion.objects.filter(user=user).select_related("problem")
        )
        completion_map = {completion.problem_id: completion for completion in completions}

        (
            completed_problem_ids,
            retry_problem_ids,
            weak_tag_counter,
            strong_tag_counter,
            profile,
        ) = cls._build_user_profile(completions)

        target_difficulty = difficulty or cls._infer_target_difficulty(profile)
        if strategy == "challenge" and difficulty is None:
            target_difficulty = cls._step_up_difficulty(target_difficulty)

        base_queryset = LeetCodeProblem.objects.only(
            "id",
            "problem_id",
            "title",
            "title_slug",
            "difficulty",
            "is_premium",
            "acceptance_rate",
            "tags",
        )

        if difficulty:
            base_queryset = base_queryset.filter(difficulty=difficulty)

        all_candidates = list(base_queryset)
        filtered_candidates = cls._filter_candidates(
            all_candidates=all_candidates,
            completed_problem_ids=completed_problem_ids,
            focus_tag=normalized_focus_tag,
            include_completed=include_completed,
        )

        fallback_include_completed = False
        if not filtered_candidates and not include_completed:
            filtered_candidates = cls._filter_candidates(
                all_candidates=all_candidates,
                completed_problem_ids=completed_problem_ids,
                focus_tag=normalized_focus_tag,
                include_completed=True,
            )
            fallback_include_completed = bool(filtered_candidates)

        ranked_problems = cls._rank_candidates(
            user=user,
            candidates=filtered_candidates,
            target_difficulty=target_difficulty,
            strategy=strategy,
            weak_tag_counter=weak_tag_counter,
            strong_tag_counter=strong_tag_counter,
            retry_problem_ids=retry_problem_ids,
            completion_map=completion_map,
        )

        selected = ranked_problems[:count]
        strategy_data = {
            "name": strategy,
            "focus_tag": normalized_focus_tag,
            "target_difficulty": target_difficulty,
            "requested_difficulty": difficulty,
            "include_completed": include_completed,
            "fallback_include_completed": fallback_include_completed,
            "returned_count": len(selected),
        }

        profile["target_difficulty"] = target_difficulty
        profile["weak_tags"] = [
            {"tag": tag, "weight": weight}
            for tag, weight in weak_tag_counter.most_common(5)
        ]

        return {
            "problems": selected,
            "profile": profile,
            "strategy": strategy_data,
        }

    @classmethod
    def _build_user_profile(cls, completions):
        completed_problem_ids = set()
        retry_problem_ids = set()
        weak_tag_counter = Counter()
        strong_tag_counter = Counter()
        completed_by_difficulty = Counter()
        status_counter = Counter()

        for completion in completions:
            status_counter[completion.status] += 1
            problem = completion.problem
            tags = cls._normalize_tags(problem.tags)

            if completion.status == "completed":
                completed_problem_ids.add(problem.id)
                completed_by_difficulty[problem.difficulty] += 1
                for tag in tags:
                    strong_tag_counter[tag] += 1
                continue

            if completion.status in {"failed", "in_progress"}:
                retry_problem_ids.add(problem.id)
                weight = max(1, completion.attempts)
                for tag in tags:
                    weak_tag_counter[tag] += weight

        profile = {
            "total_attempted": len(completions),
            "total_completed": status_counter.get("completed", 0),
            "total_in_progress": status_counter.get("in_progress", 0),
            "total_failed": status_counter.get("failed", 0),
            "completed_by_difficulty": {
                "easy": completed_by_difficulty.get("easy", 0),
                "medium": completed_by_difficulty.get("medium", 0),
                "hard": completed_by_difficulty.get("hard", 0),
            },
        }

        return (
            completed_problem_ids,
            retry_problem_ids,
            weak_tag_counter,
            strong_tag_counter,
            profile,
        )

    @classmethod
    def _infer_target_difficulty(cls, profile):
        total_completed = profile.get("total_completed", 0)
        completed_by_difficulty = profile.get("completed_by_difficulty", {})

        easy_done = completed_by_difficulty.get("easy", 0)
        medium_done = completed_by_difficulty.get("medium", 0)
        hard_done = completed_by_difficulty.get("hard", 0)

        if total_completed < 5:
            return "easy"
        if total_completed < 20:
            return "medium" if easy_done >= medium_done else "easy"
        if hard_done < max(1, medium_done // 2):
            return "hard"
        return "medium"

    @classmethod
    def _step_up_difficulty(cls, difficulty):
        level = cls._DIFFICULTY_LEVEL.get(difficulty, 0)
        return cls._LEVEL_TO_DIFFICULTY[min(2, level + 1)]

    @classmethod
    def _filter_candidates(
        cls,
        *,
        all_candidates,
        completed_problem_ids,
        focus_tag,
        include_completed,
    ):
        filtered = []

        for problem in all_candidates:
            if not include_completed and problem.id in completed_problem_ids:
                continue

            tags = cls._normalize_tags(problem.tags)
            if focus_tag and focus_tag not in tags:
                continue

            filtered.append(problem)

        return filtered

    @classmethod
    def _rank_candidates(
        cls,
        *,
        user,
        candidates,
        target_difficulty,
        strategy,
        weak_tag_counter,
        strong_tag_counter,
        retry_problem_ids,
        completion_map,
    ):
        ranked = []
        weights = cls._STRATEGY_WEIGHTS[strategy]

        for problem in candidates:
            tags = cls._normalize_tags(problem.tags)
            overlap_tags = [tag for tag in tags if tag in weak_tag_counter]
            score = 0.0
            reasons = []
            completion = completion_map.get(problem.id)

            if problem.id in retry_problem_ids:
                score += weights["retry"]
                reasons.append("Historical block point detected; retry is recommended")

            if completion and completion.status == "failed":
                score += 12 + min(completion.attempts, 6)
                reasons.append("You have multiple failed attempts on this problem")
            elif completion and completion.status == "in_progress":
                score += 4

            if overlap_tags:
                overlap_weight = sum(min(4, weak_tag_counter[tag]) for tag in overlap_tags)
                score += min(60, overlap_weight * weights["weak_tag"])
                reasons.append(f"Covers weak tags: {', '.join(overlap_tags[:2])}")

            difficulty_distance = abs(
                cls._DIFFICULTY_LEVEL.get(problem.difficulty, 0)
                - cls._DIFFICULTY_LEVEL.get(target_difficulty, 0)
            )
            if difficulty_distance == 0:
                score += weights["difficulty_exact"]
                reasons.append(f"Difficulty matches your target level ({target_difficulty})")
            elif difficulty_distance == 1:
                score += weights["difficulty_near"]

            if tags and not any(tag in strong_tag_counter for tag in tags):
                score += weights["novelty"]

            score += cls._acceptance_rate_bonus(problem, target_difficulty)
            score += cls._stable_jitter(user_id=user.id, problem_id=problem.problem_id)

            recommendation_type = cls._recommendation_type(
                is_retry=problem.id in retry_problem_ids,
                has_weak_tag=bool(overlap_tags),
                difficulty_distance=difficulty_distance,
            )
            recommendation_reason = "; ".join(reasons[:2]) or "Matches your current learning stage"

            problem._recommendation_score = round(score, 2)
            problem._recommendation_type = recommendation_type
            problem._recommendation_reason = recommendation_reason
            problem._cached_completion = completion
            ranked.append(problem)

        ranked.sort(key=lambda item: (-item._recommendation_score, item.problem_id))
        return ranked

    @classmethod
    def _acceptance_rate_bonus(cls, problem, target_difficulty):
        acceptance_target = {"easy": 72, "medium": 56, "hard": 38}
        desired = acceptance_target.get(target_difficulty, 56)
        actual = float(problem.acceptance_rate or 0.0)
        distance = abs(actual - desired)
        return max(0.0, 12.0 - distance / 6.0)

    @staticmethod
    def _stable_jitter(*, user_id, problem_id):
        seed = f"{user_id}:{problem_id}"
        digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
        return int(digest[:2], 16) / 255.0

    @staticmethod
    def _recommendation_type(*, is_retry, has_weak_tag, difficulty_distance):
        if is_retry:
            return "retry"
        if has_weak_tag:
            return "weakness_boost"
        if difficulty_distance == 0:
            return "level_match"
        return "explore"

    @staticmethod
    def _normalize_tags(tags):
        if not isinstance(tags, list):
            return []

        normalized = []
        for tag in tags:
            normalized_tag = PersonalizedExerciseService._normalize_tag(tag)
            if normalized_tag:
                normalized.append(normalized_tag)
        return normalized

    @staticmethod
    def _normalize_tag(tag):
        if tag is None:
            return None
        value = str(tag).strip().lower()
        return value or None
