
class TestRutaAvisos:
    """Pruebas para la ruta /avisos"""
    
    def test_avisos_acceso_exitoso(self, client):
        """Verifica que la ruta /avisos retorna status 200"""
        response = client.get('/avisos')
        assert response.status_code == 200
    
    def test_avisos_retorna_html(self, client):
        """Verifica que /avisos retorna HTML"""
        response = client.get('/avisos')
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
