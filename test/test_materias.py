class TestRutaMaterias:
    """Pruebas para la ruta /materias"""
    
    def test_materias_acceso_exitoso(self, client):
        """Verifica que la ruta /materias retorna status 200"""
        response = client.get('/materias')
        assert response.status_code == 200
    
    def test_materias_retorna_html(self, client):
        """Verifica que /materias retorna HTML"""
        response = client.get('/materias')
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
    
    def test_materias_sin_parametros(self, client):
        """Verifica que /materias funciona sin parámetros"""
        response = client.get('/materias')
        assert response.status_code == 200
    
    def test_materias_metodo_post_no_permitido(self, client):
        """Verifica que POST no está permitido"""
        response = client.post('/materias')
        assert response.status_code in [405, 404]
