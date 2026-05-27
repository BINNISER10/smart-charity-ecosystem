import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard      from './pages/Dashboard'
import Beneficiaries  from './pages/Beneficiaries'
import Applications   from './pages/Applications'
import Finance        from './pages/Finance'
import Sectors        from './pages/Sectors'
import ZakatCalc      from './pages/ZakatCalc'
import AuditLog       from './pages/AuditLog'
import Alerts         from './pages/Alerts'
import Config         from './pages/Config'
import Donors         from './pages/Donors'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index                   element={<Dashboard />} />
          <Route path="beneficiaries"    element={<Beneficiaries />} />
          <Route path="applications"     element={<Applications />} />
          <Route path="finance"          element={<Finance />} />
          <Route path="sectors"          element={<Sectors />} />
          <Route path="zakat"            element={<ZakatCalc />} />
          <Route path="audit"            element={<AuditLog />} />
          <Route path="alerts"           element={<Alerts />} />
          <Route path="config"           element={<Config />} />
          <Route path="donors"           element={<Donors />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
