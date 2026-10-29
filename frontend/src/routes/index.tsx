import { createBrowserRouter, Navigate } from 'react-router-dom';
import { RootLayout } from '../layouts/RootLayout';
import { OverviewPage } from '../pages/OverviewPage';
import { ScenariosPage } from '../pages/ScenariosPage';
import { AlertsPage } from '../pages/AlertsPage';
import { CasesPage } from '../pages/CasesPage';
import { InvestigationPage } from '../pages/InvestigationPage';
import { EvaluationPage } from '../pages/EvaluationPage';
import { CBDCProvenancePage } from '../pages/CBDCProvenancePage';
import { NotFoundPage } from '../pages/NotFoundPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/current-money/overview" replace />,
      },
      // Current Money Routes
      {
        path: 'current-money/overview',
        element: <OverviewPage />,
      },
      {
        path: 'current-money/scenarios',
        element: <ScenariosPage />,
      },
      {
        path: 'current-money/alerts',
        element: <AlertsPage />,
      },
      {
        path: 'current-money/cases',
        element: <CasesPage />,
      },
      {
        path: 'current-money/investigation',
        element: <InvestigationPage />,
      },
      {
        path: 'current-money/evaluation',
        element: <EvaluationPage />,
      },
      // CBDC Tokens Routes
      {
        path: 'cbdc/overview',
        element: <OverviewPage />,
      },
      {
        path: 'cbdc/scenarios',
        element: <ScenariosPage />,
      },
      {
        path: 'cbdc/alerts',
        element: <AlertsPage />,
      },
      {
        path: 'cbdc/cases',
        element: <CasesPage />,
      },
      {
        path: 'cbdc/investigation',
        element: <InvestigationPage />,
      },
      {
        path: 'cbdc/provenance',
        element: <CBDCProvenancePage />,
      },
      {
        path: 'cbdc/evaluation',
        element: <EvaluationPage />,
      },
      // 404
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);
