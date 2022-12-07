use pyo3::prelude::{pyfunction, pymodule, Python, PyResult, PyErr, wrap_pyfunction, PyModule};
use pyo3::types::{PyList};
use pyo3::exceptions;
mod dubins;
mod vana;

#[pyfunction]
fn hello_python(val: &str) -> PyResult<String> {
    Ok(format!("Hello Python {}!", val))
}

#[pyfunction]
fn vana_airplane(_py: Python, start: &PyList, end: &PyList, radius: f64, fa_min: f64, fa_max: f64) -> PyResult<vana::VanaPath> {
    let s: Vec<f64>= start.extract()?;
    let e: Vec<f64> = end.extract()?;
    match vana::vana_airplane(&s, &e, radius, fa_min, fa_max) {
        Ok(x) => return Ok(x),
        Err(_) => return Err(PyErr::new::<exceptions::PyException, _>("Vana Path Calculation Failed"))
    }
}

#[pyfunction]
fn dubins_car(_py: Python, start: &PyList, end: &PyList, radius: f64) -> PyResult<dubins::DubinsPath> {
    let s: Vec<f64>= start.extract()?;
    let e: Vec<f64> = end.extract()?;
    match dubins::dubins_car(&s, &e, radius) {
        Ok(x) => Ok(x),
        Err(_) => return Err(PyErr::new::<exceptions::PyException, _>("Dubins Path Calculation Failed"))
    }
}

#[pymodule]
#[pyo3(name = "dubins_rust")]
fn libdubinsrust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello_python, m)?)?;
    m.add_function(wrap_pyfunction!(dubins_car, m)?)?;
    m.add_function(wrap_pyfunction!(vana_airplane, m)?)?;
    m.add_class::<dubins::DubinsPath>()?;
    m.add_class::<vana::VanaPath>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::f64::consts::{PI};
    // #[test]
    // fn long1() {
    //     let r = match crate::vana::vana_airplane(
    //         &vec![200.0_f64, 500.0, 200.0, PI, -PI / 36.0],
    //         &vec![500_f64, 350.0, 100.0, 0.0, -PI / 36.0],
    //         40.0,
    //         -PI / 12.0,
    //         PI / 9.0
    //     ) {
    //         Ok(x) => x,
    //         Err(_) => panic!("No errors allowed")
    //     };
    //     assert!(r.cost - 446.04 < 1e-4);
    // }

    // #[test]
    // fn error1() {
    //     let r = match crate::vana::vana_airplane(
    //         &vec![80.59687215275329, 32.286361691640664, 247.52742703941357, 0.0, 0.0],
    //         &vec![-326.7959347189586, -571.3061498293939, 230.35143051433937, 0.0, 0.0],
    //         40.0,
    //         -PI / 12.0,
    //         PI / 9.0
    //     ) {
    //         Ok(x) => x,
    //         Err(_) => panic!("No errors allowed")
    //     };
    //     assert!(!r.cost.is_infinite());
    // }

    // #[test]
    // fn error2() {
    //     let r = match crate::vana::vana_airplane(
    //         &vec![126.50888101324021, -76.86291046084948, 164.97752400000002, 1.5707963267948966, 0.0],
    //         &vec![-719.6339086693398, -375.3886502558864, 230.35142137351704, 0.0, 0.0],
    //         40.0,
    //         -PI / 12.0,
    //         PI / 9.0
    //     ) {
    //         Ok(x) => x,
    //         Err(_) => panic!("No errors allowed")
    //     };
    //     assert!(!r.cost.is_infinite());
    // }
    #[test]
    fn error3() {
        let r = match crate::vana::vana_airplane(
            &vec![-616.624003991396, 2582.407241303297, 217.29946090698243, 6.026221108749451, -0.2617993877991494],
            &vec![-479.0339057468126, 2546.514980762254, 151.99994812011718, 6.026221108749451, -0.2617993877991494],
            40.0,
            -PI / 12.0,
            PI / 9.0
        ) {
            Ok(x) => x,
            Err(_) => panic!("No errors allowed")
        };
        assert!(!r.cost.is_infinite());
    }
}