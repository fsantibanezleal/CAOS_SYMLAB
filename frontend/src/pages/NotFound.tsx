import { Link } from 'react-router-dom';

import { useLang } from '../lib/useLang';

export default function NotFound() {
  const es = useLang() === 'es';
  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{es ? 'Pagina no encontrada' : 'Page not found'}</h1>
        <p className="lede">
          {es
            ? 'Esa ruta no existe en esta aplicacion. Las seis paginas estan en la cabecera.'
            : 'That route does not exist in this application. The six pages are in the header.'}
        </p>
      </div>
      <p>
        <Link to="/">{es ? 'Volver al banco de trabajo' : 'Back to the workbench'}</Link>
      </p>
    </div>
  );
}
