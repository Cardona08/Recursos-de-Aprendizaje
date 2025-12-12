class TestRutaDocentes:
    """Pruebas para la ruta /docentes"""
    
    def test_docentes_acceso_exitoso(self, client):
        """Verifica que la ruta /docentes retorna status 200"""
        response = client.get('/docentes')
        assert response.status_code == 200
    
    def test_docentes_retorna_html(self, client):
        """Verifica que /docentes retorna HTML"""
        response = client.get('/docentes')
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
    
    def test_docentes_sin_parametros(self, client):
        """Verifica que /docentes funciona sin parámetros GET"""
        response = client.get('/docentes')
        assert response.status_code == 200
    
    def test_docentes_metodo_post_no_permitido(self, client):
        """Verifica que POST no está permitido en /docentes"""
        response = client.post('/docentes')
        assert response.status_code in [405, 404]
