use rand::prelude::*;
use std::{sync::mpsc, thread};

struct PMT {
    count: i64,
    time: f64,
    palse_time: f64,
    rise_times: Vec<f64>,
}

impl PMT {
    fn new(count: i64, time: f64, palse_time: f64) -> PMT {
        PMT {
            count,
            time,
            palse_time,
            rise_times: Vec::new(),
        }
    }

    fn generate_rise_times(&mut self) {
        let mut rng = rand::thread_rng();
        for _ in 0..self.count {
            let random_time = rng.gen_range(0.0..self.time);
            self.rise_times.push(random_time);
        }
        self.rise_times.sort_by(|a, b| a.partial_cmp(b).unwrap());
    }
}

// pmt1のパルスの時間がpmt2の立ち上がりに重なっているか (aの比較しかおこなっていない)
fn is_pmt1_overlaped(pmt1: &PMT, pmt2: &PMT) -> bool {
    let mut pmt2_start = 0;
    for &pmt1_rise_time in &pmt1.rise_times {
        for (i, &pmt2_rise_time) in pmt2.rise_times[pmt2_start..].iter().enumerate() {
            // println!("pmt1: {}, pmt2: {}", pmt1_rise_time, pmt2_rise_time);
            if pmt1_rise_time <= pmt2_rise_time {
                if pmt2_rise_time <= pmt1_rise_time + pmt1.palse_time {
                    return true;
                } else {
                    pmt2_start = pmt2_start + i; //
                    break;
                }
            }
        }
    }
    false
}

// 2つのPMTのパルスが重なっているか(両方の比較を行う)
fn is_overlaped(pmt1: &PMT, pmt2: &PMT) -> bool {
    is_pmt1_overlaped(pmt1, pmt2) || is_pmt1_overlaped(pmt2, pmt1)
}

#[derive(Clone, Copy)]
struct InitialCondition {
    time: f64,
    palse_time: f64,
    count: i64,
}

fn simulater(a_init: InitialCondition, b_init: InitialCondition) -> bool {
    let mut pmt_a = PMT::new(a_init.count, a_init.time, a_init.palse_time);
    let mut pmt_b = PMT::new(b_init.count, b_init.time, b_init.palse_time);

    // フォト丸のノイズの時間を生成
    pmt_a.generate_rise_times();
    pmt_b.generate_rise_times();

    // 重なっているか
    is_overlaped(&pmt_a, &pmt_b)
}

// 非並列でのモンテカルロシミュレーション
#[allow(dead_code)]
fn nonparallel_simulater(
    sample_count: i64,
    a_init: InitialCondition,
    b_init: InitialCondition,
) -> f64 {
    let mut overlapeds: Vec<bool> = Vec::new();
    for _ in 0..sample_count {
        overlapeds.push(simulater(a_init, b_init));
    }

    // 確率を計算
    let true_count = overlapeds.iter().filter(|&&x| x).count() as f64; // 重なっている = true　の数を数える
    true_count / sample_count as f64
}

fn parallel_simulater(
    sample_count: i64,
    a_init: InitialCondition,
    b_init: InitialCondition,
) -> f64 {
    let num_threads = 20;
    let samples_per_thread = sample_count / num_threads;

    let (tx, rx) = mpsc::channel();
    for _ in 0..num_threads {
        let thread_tx = tx.clone();
        let a_init = a_init.clone();
        let b_init = b_init.clone();

        thread::spawn(move || {
            let mut local_overlapeds = 0;
            for _ in 0..samples_per_thread {
                if simulater(a_init, b_init) {
                    local_overlapeds += 1;
                }
            }
            thread_tx.send(local_overlapeds).unwrap();
        });
    }

    let mut total_overlaped = 0;
    for _ in 0..num_threads {
        total_overlaped += rx.recv().unwrap();
    }

    total_overlaped as f64 / sample_count as f64
}

fn main() {
    let a_init = InitialCondition {
        time: 60.0 * 3.0 + 30.0,
        palse_time: 20.0 * 1e-9,
        count: 4645,
    };
    let b_init = InitialCondition {
        time: 60.0 * 3.0 + 30.0,
        palse_time: 20.0 * 1e-9,
        count: 3389,
    };
    let sample = 10000000;

    // let p = nonparallel_simulater(sample, a_init, b_init);
    let p = parallel_simulater(sample, a_init, b_init);
    println!("{} %", p * 100.0);
}

// テスト
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_overlaped() {
        let time = 10.0;
        let palse_time = 0.5; // 0.5s
        let count = 5;

        let mut pmt_a = PMT::new(count, time, palse_time);
        let mut pmt_b = PMT::new(count, time, palse_time);

        // rise_timesを手動で設定(普通はgenerate_rise_timesを使う)
        pmt_a.rise_times = vec![1.0, 3.0, 5.0, 7.0, 9.0];
        pmt_b.rise_times = vec![2.0, 4.0, 6.0, 8.0, 9.2];

        // Aの9.0sとBの9.2sが重なっている(9.0s < 9.2s < 9.0s + 0.5s)
        let a_is_over = is_pmt1_overlaped(&pmt_a, &pmt_b);
        assert_eq!(a_is_over, true);

        // BはAと重なっていない
        let b_is_over = is_pmt1_overlaped(&pmt_b, &pmt_a);
        assert_eq!(b_is_over, false);

        // AとBは重なっている
        let is_over = is_overlaped(&pmt_a, &pmt_b);
        assert_eq!(is_over, true);
    }
}
