use rand::prelude::*;
use std::{sync::mpsc, thread};

#[derive(Clone, Debug)]
struct Palse {
    rise_time: f64,
    width: f64,
}

struct PMT {
    palse_times: Vec<Palse>,
}

impl PMT {
    fn new(count: i64, time: f64, palse_time: f64) -> PMT {
        let mut rise_times = Vec::new();
        let mut palse_times: Vec<Palse> = Vec::new();

        // ランダムの立ち上がり時間を生成
        let mut rng = rand::thread_rng();
        for _ in 0..count {
            let random_time = rng.gen_range(0.0..time);
            rise_times.push(random_time);
        }
        rise_times.sort_by(|a, b| a.partial_cmp(b).unwrap());

        // パルスの長さは同じ
        for rise_time in rise_times {
            palse_times.push(Palse {
                rise_time: rise_time,
                width: palse_time,
            });
        }

        PMT { palse_times }
    }

    fn sort(&mut self) {
        self.palse_times
            .sort_by(|a, b| a.rise_time.partial_cmp(&b.rise_time).unwrap());
    }

    fn sync(&mut self, other_pmt: &mut PMT) -> PMT {
        PMT {
            palse_times: [self.palse_times.clone(), other_pmt.palse_times.clone()].concat(),
        }
    }
}

// pmt1のパルスがpmt2の立ち上がりに重なっているか (片方の比較しかおこなっていない)
fn overlaped_pmt1(pmt1: &PMT, pmt2: &PMT) -> PMT {
    let mut new_palse_times: Vec<Palse> = Vec::new();
    let mut pmt2_loop = 0;
    for &ref pmt1_palse in &pmt1.palse_times {
        for (i, &ref pmt2_palse) in pmt2.palse_times[pmt2_loop..].iter().enumerate() {
            let pmt1_start = pmt1_palse.rise_time;
            let pmt2_start = pmt2_palse.rise_time;
            let pmt1_end = pmt1_palse.rise_time + pmt1_palse.width;
            let pmt2_end = pmt2_palse.rise_time + pmt2_palse.width;
            // println!(
            //     "pmt1_start: {}, pmt1_end: {} || pmt2_start: {}, pmt2_end: {}",
            //     pmt1_start, pmt1_end, pmt2_start, pmt2_end
            // );
            if pmt1_start <= pmt2_start {
                if pmt2_start <= pmt1_end {
                    if pmt1_end <= pmt2_end {
                        new_palse_times.push(Palse {
                            rise_time: pmt2_start,
                            width: pmt1_end - pmt2_start,
                        })
                    } else {
                        new_palse_times.push(Palse {
                            rise_time: pmt2_start,
                            width: pmt2_end - pmt2_start,
                        })
                    }
                } else {
                    pmt2_loop = pmt2_loop + i; //
                    break;
                }
            }
        }
    }
    // println!("new_palse_times: {:?}", new_palse_times);
    PMT {
        palse_times: new_palse_times,
    }
}

// 2つのPMTのパルスが重なっているか(両方の比較を行う)
fn overlaped_pmt(pmt1: &PMT, pmt2: &PMT) -> PMT {
    let mut over_pmt1 = overlaped_pmt1(&pmt1, &pmt2);
    let mut over_pmt2 = overlaped_pmt1(&pmt2, &pmt1);
    let mut sync_pmt = over_pmt1.sync(&mut over_pmt2);
    sync_pmt.sort();
    sync_pmt
}

fn is_all_overlaped_pmt(pmt1: &PMT, pmt2: &PMT, pmt3: &PMT) -> bool {
    let pmt12 = overlaped_pmt(&pmt1, &pmt2);
    let pmt123 = overlaped_pmt(&pmt12, &pmt3);
    if pmt123.palse_times.len() > 0 {
        true
    } else {
        false
    }
}

#[derive(Clone, Copy)]
struct InitialCondition {
    time: f64,
    palse_time: f64,
    count: i64,
}

fn simulater(a_init: InitialCondition, b_init: InitialCondition, c_init: InitialCondition) -> bool {
    let pmt_a = PMT::new(a_init.count, a_init.time, a_init.palse_time);
    let pmt_b = PMT::new(b_init.count, b_init.time, b_init.palse_time);
    let pmt_c = PMT::new(c_init.count, c_init.time, c_init.palse_time);

    is_all_overlaped_pmt(&pmt_a, &pmt_b, &pmt_c)
}

fn parallel_simulater(
    sample_count: i64,
    a_init: InitialCondition,
    b_init: InitialCondition,
    c_init: InitialCondition,
) -> f64 {
    let num_threads = 20;
    let samples_per_thread = sample_count / num_threads;

    let (tx, rx) = mpsc::channel();
    for _ in 0..num_threads {
        let thread_tx = tx.clone();
        let a_init = a_init.clone();
        let b_init = b_init.clone();
        let c_init = c_init.clone();

        thread::spawn(move || {
            let mut local_overlapeds = 0;
            for _ in 0..samples_per_thread {
                if simulater(a_init, b_init, c_init) {
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
        time: 60.0,
        palse_time: 20.0 * 1e-9,
        count: 600,
    };
    let b_init = a_init.clone();
    let c_init = a_init.clone();

    let sample_count = 10000000;
    let p = parallel_simulater(sample_count, a_init, b_init, c_init);
    println!("result: {} %", p * 100.0);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_overlaped_pmt() {
        let pmt_a = PMT {
            palse_times: vec![
                Palse {
                    rise_time: 0.0,
                    width: 2.0,
                },
                Palse {
                    rise_time: 7.0,
                    width: 1.0,
                },
                Palse {
                    rise_time: 100.0,
                    width: 1.0,
                },
            ],
        };

        let pmt_b = PMT {
            palse_times: vec![
                Palse {
                    rise_time: 1.0,
                    width: 1.0,
                },
                Palse {
                    rise_time: 6.0,
                    width: 2.0,
                },
            ],
        };

        let pmt_c = PMT {
            palse_times: vec![Palse {
                rise_time: 1.0,
                width: 0.5,
            }],
        };

        // overlaped_pmt1のテスト
        let over_pmt_a = overlaped_pmt1(&pmt_a, &pmt_b);
        assert_eq!(over_pmt_a.palse_times[0].rise_time, 1.0);
        assert_eq!(over_pmt_a.palse_times[0].width, 1.0);
        // 重なっているのは1つ
        assert_eq!(over_pmt_a.palse_times.len(), 1);

        // overlaped_pmtのテスト
        let over_pmt = overlaped_pmt(&pmt_a, &pmt_b);
        // 浮動小数点の計算誤差を考慮(roundで四捨五入)
        assert_eq!(over_pmt.palse_times[0].rise_time.round(), 1.0);
        assert_eq!(over_pmt.palse_times[0].width.round(), 1.0);
        assert_eq!(over_pmt.palse_times[1].rise_time.round(), 7.0);
        assert_eq!(over_pmt.palse_times[1].width.round(), 1.0);

        // is_all_overlaped_pmtのテスト
        let is_over = is_all_overlaped_pmt(&pmt_a, &pmt_b, &pmt_c);
        assert_eq!(is_over, true);
    }
}
