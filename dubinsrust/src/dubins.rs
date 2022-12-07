use std::f64::consts::{PI, FRAC_PI_2};
use pyo3::prelude::{pyclass};


const APPROX_ZERO: f64 = 1e-6;

#[pyclass]
#[derive(Clone)]
pub enum DubinsPathType {
    UNKNOWN = 0,
    LSL = 1,
    LSR = 2,
    RSL = 3,
    RSR = 4,
    LRL = 5,
    RLR = 6
}

#[pyclass]
#[derive(Clone)]
pub struct DubinsPath {
    #[pyo3(get, set)]
    pub a: f64,
    #[pyo3(get, set)]
    pub b: f64,
    #[pyo3(get, set)]
    pub c: f64, 
    #[pyo3(get, set)]
    pub cost: f64,
    #[pyo3(get, set)]
    pub path_type: DubinsPathType
}

impl DubinsPath {
    pub fn new(path_type: DubinsPathType) -> DubinsPath {
        DubinsPath {
            a: 0.0,
            b: 0.0,
            c: 0.0,
            cost: f64::INFINITY,
            path_type: path_type
        }
    }
}

pub fn dubins_car(start: &Vec<f64>, end: &Vec<f64>, radius: f64) -> Result<DubinsPath, &'static str> {
    let (x, y, h) = normalize(start, end, radius);

    let m_cth = h.cos();
    let m_sth = h.sin();

    let mut results: [DubinsPath; 6] = [
        solve_lsl(x, y, h, m_cth, m_sth),
        solve_lsr(x, y, h, m_cth, m_sth),
        solve_rsl(x, y, h, m_cth, m_sth),
        solve_rsr(x, y, h, m_cth, m_sth),
        solve_lrl(x, y, h),
        solver_rlr(x, y, h)
    ];
    results.sort_by(| a, b | a.cost.partial_cmp(&b.cost).unwrap());
    if results[0].cost.is_infinite() {
        Err("no valid path")
    } else {
        Ok(DubinsPath {
            a: results[0].a * radius,
            b: results[0].b * radius,
            c: results[0].c * radius,
            cost: results[0].cost * radius,
            path_type: results[0].path_type.clone()
        })
    }

}

fn solve_lsl(x: f64, y: f64, h:f64, m_cth: f64, m_sth: f64) -> DubinsPath {
    let b = ((x - m_sth).powi(2) + (y + m_cth - 1.0).powi(2)).sqrt();
    let mut a0 = (y + m_cth - 1.0).atan2( x - m_sth);
    let mut r = DubinsPath::new(DubinsPathType::LSL);

    if a0.is_nan() {
        return r
    }

    while a0 < 0.0 {
        a0 += PI;
    }

    for a in [a0, a0 + PI].iter() {
        let c = (h - a).rem_euclid(2.0 * PI);
        let end = get_endpoint_bsb(*a, b, c, 1.0, 1.0);
        if compare_vector(&end, x, y, h) == 0.0 {
            r = DubinsPath {a: *a, b: b, c: c, cost: a + b + c, path_type: DubinsPathType::LSL};
        }
    }
    r
}

fn solve_lsr(x: f64, y: f64, h:f64, m_cth: f64, m_sth: f64) -> DubinsPath {
    let b = ((x + m_sth).powi(2) + (y - m_cth - 1.0).powi(2) - 4.0).sqrt();
    let mut a0 = (2.0 * (x + m_sth) + b * (y - m_cth - 1.0)).atan2(b * (x + m_sth) - 2.0 * (y - m_cth - 1.0));
    let mut r = DubinsPath::new(DubinsPathType::LSR);

    if a0.is_nan() {
        return r
    }

    while a0 < 0.0 {
        a0 += PI;
    }

    for a in [a0, a0 + PI].iter() {
        let c = (a - h).rem_euclid(2.0 * PI);
        let end = get_endpoint_bsb(*a, b, c, 1.0, -1.0);
        if compare_vector(&end, x, y, h)  == 0.0 {
            r = DubinsPath {a: *a, b: b, c: c, cost: a + b + c, path_type: DubinsPathType::LSR};
        }
    }
    r
}

fn solve_rsl(x: f64, y: f64, h:f64, m_cth: f64, m_sth: f64) -> DubinsPath {
    let b = ((x - m_sth).powi(2) + (y + m_cth + 1.0).powi(2) - 4.0).sqrt();
    let mut a0 = (2.0 * (x - m_sth) - b * (y + m_cth + 1.0)).atan2(b * (x - m_sth) + 2.0 * (y + m_cth + 1.0));
    let mut r = DubinsPath::new(DubinsPathType::RSL);

    if a0.is_nan() {
        return r
    }

    while a0 < 0.0 {
        a0 += PI;
    }

    for a in [a0, a0 + PI].iter() {
        let c = (h + a).rem_euclid(2.0 * PI);
        let end = get_endpoint_bsb(*a, b, c, -1.0, 1.0);
        if compare_vector(&end, x, y, h)  == 0.0 {
            r = DubinsPath {a: *a, b: b, c: c, cost: a + b + c, path_type: DubinsPathType::RSL};
        }
    }
    r
}

fn solve_rsr(x: f64, y: f64, h:f64, m_cth: f64, m_sth: f64) -> DubinsPath {
    let b = ((x + m_sth).powi(2) + (y - m_cth + 1.0).powi(2)).sqrt();
    let mut a0 = (m_cth - y - 1.0).atan2(x + m_sth);
    let mut r = DubinsPath::new(DubinsPathType::RSR);

    if a0.is_nan() {
        return r
    }

    while a0 < 0.0 {
        a0 += PI;
    }

    for a in [a0, a0 + PI].iter() {
        let c = if a.abs() < APPROX_ZERO {
            if h.abs() < APPROX_ZERO {
                0.0
            } else {
                2.0 * PI
            }
        } else {
            let h_cw = 2.0 * PI - h.rem_euclid(2.0 * PI);
            if a >= &h_cw {
                h_cw + 2.0 * PI - a
            } else {
                2.0 * PI - h - a
            }
        };
        let end = get_endpoint_bsb(*a, b, c, -1.0, -1.0);
        if compare_vector(&end, x, y, h)  == 0.0 {
            r = DubinsPath {a: *a, b: b, c: c, cost: a + b + c, path_type: DubinsPathType::RSR};
        }
    }
    r
}

fn solver_rlr(x: f64, y: f64, h: f64) -> DubinsPath {
    let v = (x + h.sin()) * 0.5;
    let w = (-y - 1.0 + h.cos()) * 0.5;
    let b0 = (1.0 - (v.powi(2) + w.powi(2)) * 0.5).acos().abs();
    let mut r = DubinsPath::new(DubinsPathType::RLR);
    if b0.is_nan() {
        return r
    }

    for b in [b0, 2.0 * PI - b0].iter() {
        let s = (v.powi(2) - w.powi(2)) / (2.0 * (1.0 - b.cos()));
        let t = v * w / (1.0 - b.cos());
        let mut a0: f64 = 0.5 * (t * b.cos() + s * b.sin()).atan2(s * b.cos() - t * b.sin());

        if a0.is_nan() {
            continue;
        }

        while a0 < 0.0 {
            a0 += FRAC_PI_2;
        }

        let aa = [
            a0.rem_euclid(2.0 * PI),
            (a0 + FRAC_PI_2).rem_euclid(2.0 * PI),
            (a0 + PI).rem_euclid(2.0 * PI),
            (a0 + 3.0 * FRAC_PI_2).rem_euclid(2.0 * PI)
        ];
        for a in aa.iter() {
            let c = (b - a - h).rem_euclid(2.0 * PI);
            let end = get_endpoint_bbb(*a, *b, c, -1.0, 1.0, -1.0);
            if compare_vector(&end, x, y, h) == 0.0 && f64::max(*a, c) < *b && f64::min(*a, c) < *b + PI {
                r = DubinsPath {a: *a, b: *b, c: c, cost: a + b + c, path_type: DubinsPathType::RLR};
            }
        }
    }
    r
}

fn solve_lrl(x: f64, y: f64, h: f64) -> DubinsPath {
    let v = (x - h.sin()) * 0.5;
    let w = (y - 1.0 + h.cos()) * 0.5;
    let b0 = (1.0 - (v.powi(2) + w.powi(2)) * 0.5).acos().abs();
    let mut r = DubinsPath::new(DubinsPathType::LRL);
    if b0.is_nan() {
        return r
    }

    for b in [b0, 2.0 * PI - b0].iter() {
        let s = (v.powi(2) - w.powi(2)) / (2.0 * (1.0 - b.cos()));
        let t = v * w / (1.0 - b.cos());
        let mut a0: f64 = 0.5 * (t * b.cos() + s * b.sin()).atan2(s * b.cos() - t * b.sin());

        if a0.is_nan() {
            continue;
        }

        while a0 < 0.0 {
            a0 += FRAC_PI_2;
        }

        let aa = [
            a0.rem_euclid(2.0 * PI),
            (a0 + FRAC_PI_2).rem_euclid(2.0 * PI),
            (a0 + PI).rem_euclid(2.0 * PI),
            (a0 + 3.0 * FRAC_PI_2).rem_euclid(2.0 * PI)
        ];
        for a in aa.iter() {
            let c = (b - a + h).rem_euclid(2.0 * PI);
            let end = get_endpoint_bbb(*a, *b, c, 1.0, -1.0, 1.0);
            if compare_vector(&end, x, y, h) == 0.0 && f64::max(*a, c) < *b && f64::min(*a, c) < b + PI {
                r = DubinsPath {a: *a, b: *b, c: c, cost: a + b + c, path_type: DubinsPathType::LRL};
            }
        }
    }
    r
}


fn normalize(s: &Vec<f64>, e: &Vec<f64>, r: f64) -> (f64, f64, f64) {
    let u = (e[0] - s[0]) / r;
    let v = (e[1] - s[1]) / r;
    let x = u * s[2].cos() + v * s[2].sin();
    let y = -u * s[2].sin() + v * s[2].cos();
    let h = (e[2] - s[2]).rem_euclid(2.0 * PI);
    (x, y, h)
}

fn get_endpoint_bsb(a: f64, b: f64, c: f64, ki: f64, kf: f64) -> [f64;3] {
    let mut p: [f64; 3] = [0.0; 3];
    let a = a * ki;
    let c = c * kf;
    p[0] = ki * a.sin() + b * a.cos() + kf * ((a + c).sin() - a.sin());
    p[1] = ki * (-a.cos() + 1.0) + b * a.sin() + kf * (-(a + c).cos() + a.cos());
    p[2] = (a + c).rem_euclid(2.0 * PI);
    p
}

fn get_endpoint_bbb(a: f64, b: f64, c: f64, ki: f64, km: f64, kf: f64) -> [f64;3] {
    let mut p: [f64; 3] = [0.0; 3];
    let a = a * ki;
    let b = b * km;
    let c = c * kf;
    p[0] = ki * (2.0 * a.sin() - 2.0 * (a + b).sin() + (a + b + c).sin());
    p[1] = ki * (1.0 - 2.0 * a.cos() + 2.0 * (a + b).cos() - (a + b + c).cos());
    p[2] = (a + b + c).rem_euclid(2.0 * PI);
    p
}

fn compare_vector(a: &[f64;3], x: f64, y: f64, h: f64) -> f64{
    let r = (a[0] - x).powi(2) + (a[1] - y).powi(2) + (a[2] - h).powi(2);
    if r < APPROX_ZERO {
        0.0
    } else {
        r
    }
}
