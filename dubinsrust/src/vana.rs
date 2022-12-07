use crate::dubins;
use pyo3::prelude::{pyclass};

const MAX_ITER: u32 = 1000;
const APPROX_ZERO: f64 = 0.1e-10;

#[pyclass]
pub struct VanaPath {
    #[pyo3(get, set)]
    pub a: f64,
    #[pyo3(get, set)]
    pub b: f64,
    #[pyo3(get, set)]
    pub c: f64,
    #[pyo3(get, set)]
    pub d: f64,
    #[pyo3(get, set)]
    pub e: f64,
    #[pyo3(get, set)]
    pub f: f64,
    #[pyo3(get, set)]
    pub cost: f64,
    #[pyo3(get, set)]
    pub radius: f64,
    #[pyo3(get, set)]
    pub radius_z: f64,
    #[pyo3(get, set)]
    pub path_type: dubins::DubinsPathType,
    #[pyo3(get, set)]
    pub path_type_z: dubins::DubinsPathType,
}


pub fn vana_airplane(start: &Vec<f64>, end: &Vec<f64>, min_radius: f64, fa_min: f64, fa_max: f64) -> Result<VanaPath, &'static str> {
    let mut b = 2.0;
    let mut vert_radius = 1.0 / (min_radius.powi(-2) - (min_radius * b).powi(-2)).sqrt();
    let (mut xy_path, mut sz_path) = decoupled(start, end, b * min_radius, vert_radius);
    let mut i = 0;
    while !is_feasible(&sz_path, fa_min, fa_max, start[4], vert_radius) && i < MAX_ITER {
        i += 1;
        b *= 2.0;
        vert_radius = 1.0 / (min_radius.powi(-2) - (min_radius * b).powi(-2)).sqrt();
        (xy_path, sz_path) = decoupled(start, end, min_radius * b, vert_radius);
    }

    if i >= MAX_ITER {
        return Err("couldn't find valid path")
    }

    let mut delta = 0.1_f64;
    i = 0;
    while delta.abs() > APPROX_ZERO && i < MAX_ITER {
        let c = 1_f64.max(b + delta);
        vert_radius = 1.0 / (min_radius.powi(-2) - (min_radius * c).powi(-2)).sqrt();
        let (xy_path_p, sz_path_p) = decoupled(start, end, min_radius * c, vert_radius);
        if is_feasible(&sz_path_p, fa_min, fa_max, start[4], vert_radius) && sz_path_p.cost < sz_path.cost {
            xy_path = xy_path_p;
            sz_path = sz_path_p;
            b = c;
            delta *= 2.0;
        } else {
            delta *= -0.1;
        }
        i += 1;
    }
    if i >= MAX_ITER {
        return Err("couldn't find valid path")
    }
    vert_radius = 1.0 / (min_radius.powi(-2) - (min_radius * b).powi(-2)).sqrt();
    Ok(VanaPath {
        a: xy_path.a,
        b: xy_path.b,
        c: xy_path.c,
        d: sz_path.a,
        e: sz_path.b,
        f: sz_path.c,
        path_type: xy_path.path_type.clone(),
        path_type_z: sz_path.path_type.clone(),
        cost: sz_path.cost,
        radius: b * min_radius,
        radius_z: vert_radius
    })
    
}

fn decoupled(start: &Vec<f64>, end: &Vec<f64>, horz_radius: f64, vert_radius: f64) -> (dubins::DubinsPath, dubins::DubinsPath) {
    let xy_s = vec![start[0], start[1], start[3]];
    let xy_e = vec![end[0], end[1], end[3]];
    let xy_path = match dubins::dubins_car(&xy_s, &xy_e, horz_radius) {
        Ok(x) => x,
        Err(_) => {
            return (dubins::DubinsPath::new(dubins::DubinsPathType::UNKNOWN),  dubins::DubinsPath::new(dubins::DubinsPathType::UNKNOWN))
        }
    };
    if vert_radius.is_infinite() {
        return (xy_path, dubins::DubinsPath::new(dubins::DubinsPathType::UNKNOWN))
    }
    let sz_s = vec![0.0, start[2], start[4]];
    let sz_e = vec![xy_path.cost, end[2], end[4]];
    let sz_path = match dubins::dubins_car(&sz_s, &sz_e, vert_radius) {
        Ok(x) => x,
        Err(_) => {
            return (dubins::DubinsPath::new(dubins::DubinsPathType::UNKNOWN),  dubins::DubinsPath::new(dubins::DubinsPathType::UNKNOWN))
        }
    };
    (xy_path, sz_path)
}

fn is_feasible(path: &dubins::DubinsPath, fa_min: f64, fa_max: f64, heading: f64, radius: f64) -> bool {
    match path.path_type {
        dubins::DubinsPathType::RLR => false,
        dubins::DubinsPathType::LRL => false,
        dubins::DubinsPathType::UNKNOWN => false,
        dubins::DubinsPathType::RSL | dubins::DubinsPathType::RSR => {
            heading - path.a / radius > fa_min
        },
        dubins::DubinsPathType::LSL | dubins::DubinsPathType::LSR => {
            heading + path.a / radius < fa_max
        }
    }
}