
class TestRutaOrientadores:
    """Pruebas para la ruta /orientadores"""
    
    def test_orientadores_acceso_exitoso(self, client):
        """Verifica que la ruta /orientadores retorna status 200"""
        response = client.get('/orientadores')
        assert response.status_code == 200
    
    def test_orientadores_retorna_html(self, client):
        """Verifica que /orientadores retorna HTML"""
        response = client.get('/orientadores')
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
    
    def test_orientadores_sin_parametros(self, client):
        """Verifica que /orientadores funciona sin parámetros"""
        response = client.get('/orientadores')
        assert response.status_code == 200
    
    def test_orientadores_metodo_post_no_permitido(self, client):
        """Verifica que POST no está permitido"""
        response = client.post('/orientadores')
        assert response.status_code in [405, 404]
