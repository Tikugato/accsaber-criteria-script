import numpy as np
import pandas as pd


class FeatureBuilder:
    def _unique_times(self, times, decimals=6):
        if len(times) == 0:
            return times
        return np.unique(np.round(times.astype(float), decimals=decimals))

    def _window_count_features(self, times, total_time, window_size, prefix):
        if len(times) == 0 or total_time <= 0:
            return {
                f"{prefix}_mean": 0.0,
                f"{prefix}_std": 0.0,
                f"{prefix}_p90": 0.0,
                f"{prefix}_p95": 0.0,
                f"{prefix}_max": 0.0,
            }

        bins = np.arange(0, total_time + window_size, window_size)
        counts, _ = np.histogram(times, bins=bins)

        rate = counts / window_size

        return {
            f"{prefix}_mean": float(np.mean(rate)),
            f"{prefix}_std": float(np.std(rate)),
            f"{prefix}_p90": float(np.quantile(rate, 0.90)),
            f"{prefix}_p95": float(np.quantile(rate, 0.95)),
            f"{prefix}_max": float(np.max(rate)),
        }

    def _delta_features(self, deltas, prefix):
        return {
            f"{prefix}_mean": float(deltas.mean()),
            f"{prefix}_std": float(deltas.std(ddof=0)),
            f"{prefix}_p10": float(deltas.quantile(0.10)),
            f"{prefix}_p50": float(deltas.quantile(0.50)),
            f"{prefix}_p90": float(deltas.quantile(0.90)),
        }

    def build_map_features(self, map_object):
        df = map_object.standard_df
        stats = map_object.statistics

        note_df = df[df["is_note"]].copy()
        bomb_df = df[df["is_bomb"]].copy()
        left_df = note_df[note_df["hand"] == "left"].copy()
        right_df = note_df[note_df["hand"] == "right"].copy()

        event_total_time = float(df["seconds"].max()) if not df.empty else 0.0
        bomb_moment_times = self._unique_times(bomb_df["seconds"].to_numpy())

        left_seconds_delta = left_df["seconds"].diff().fillna(0)
        right_seconds_delta = right_df["seconds"].diff().fillna(0)

        features = {
            "num_notes": int(len(note_df)),
            "num_bombs": int(len(bomb_df)),
            "num_bomb_moments": int(len(bomb_moment_times)),
            "song_time": event_total_time,
            "njs": float(map_object.njs),

            "avg_sps": float(stats.avg_sps),
            "peak_sps": float(stats.peak_sps),
            "true_acc_avg_sps": float(stats.true_acc_avg_sps),
            "true_acc_peak_sps": float(stats.true_acc_peak_sps),

            "left_swings": int(stats.num_left_swings),
            "right_swings": int(stats.num_right_swings),
            "left_avg_sps": float(stats.left_avg_sps),
            "right_avg_sps": float(stats.right_avg_sps),

            "left_avg_angle_change": float(stats.left_avg_angle_change),
            "right_avg_angle_change": float(stats.right_avg_angle_change),
            "avg_angle_change": float(stats.avg_angle_change),

            "has_sliders": int(stats.has_sliders),

            # Use unique bomb moments for density so simultaneous bomb stacks
            # do not overwhelm the model.
            "bombs_per_second": float(len(bomb_moment_times) / max(event_total_time, 1e-6)),
            "bomb_note_ratio": float(len(bomb_df) / max(len(note_df), 1)),
            "bomb_moment_note_ratio": float(len(bomb_moment_times) / max(len(note_df), 1)),

            "left_note_ratio": float(len(left_df) / max(len(note_df), 1)),
            "right_note_ratio": float(len(right_df) / max(len(note_df), 1)),

            # Hand imbalance features
            "hand_note_imbalance": float(abs(len(left_df) - len(right_df)) / max(len(note_df), 1)),
            "hand_sps_imbalance": float(abs(stats.left_avg_sps - stats.right_avg_sps)),
            "angle_change_imbalance": float(abs(stats.left_avg_angle_change - stats.right_avg_angle_change)),
            "swing_count_imbalance": float(abs(stats.num_left_swings - stats.num_right_swings)),
        }

        # Same-hand timing delta features
        features.update(self._delta_features(left_seconds_delta, "left_seconds_delta"))
        features.update(self._delta_features(right_seconds_delta, "right_seconds_delta"))

        # Windowed note density features
        features.update(
            self._window_count_features(
                note_df["seconds"].to_numpy(),
                event_total_time,
                window_size=1.0,
                prefix="notes_per_1s",
            )
        )

        features.update(
            self._window_count_features(
                note_df["seconds"].to_numpy(),
                event_total_time,
                window_size=0.5,
                prefix="notes_per_0p5s",
            )
        )

        # Windowed bomb density features
        features.update(
            self._window_count_features(
                bomb_moment_times,
                event_total_time,
                window_size=1.0,
                prefix="bombs_per_1s",
            )
        )

        # Final cleanup
        features = {
            k: 0.0 if pd.isna(v) or np.isinf(v) else v
            for k, v in features.items()
        }

        return features
