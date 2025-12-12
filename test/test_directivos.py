class TestRutaDirectivos:
    """Pruebas para la ruta /directivos"""
    
    def test_directivos_acceso_exitoso(self, client):
        """Verifica que la ruta /directivos retorna status 200"""
        response = client.get('/directivos')
        assert response.status_code == 200
    
    def test_directivos_retorna_html(self, client):
        """Verifica que /directivos retorna HTML"""
        response = client.get('/directivos')
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
    
    def test_directivos_sin_parametros(self, client):
        """Verifica que /directivos funciona sin parámetros"""
        response = client.get('/directivos')
        assert response.status_code == 200
