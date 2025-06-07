from fastmcp import FastMCP
import httpx
from typing import Dict, Any, List
import os

mcp = FastMCP("My MCP Server")

@mcp.tool
async def list_expenses_by_user(user: str) -> List[Dict[str, Any]]:
    """
    Busca e retorna uma lista de entradas e saídas financeiras de um usuário específico.

    Faz uma requisição GET assíncrona para a API de entradas e saídas financeiras,
    filtrando os resultados pelo ID do usuário fornecido.

    Args:
        user (str): O ID do usuário cujas entradas e saídas financeiras devem ser listadas.

    Returns:
        List[Dict[str, Any]]: Uma lista de dicionários contendo os dados das entradas e saídas financeiras do usuário.
    """
    url = f"https://back-aprofunda-chat-despesa.onrender.com/despesas/{user}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    
@mcp.tool
async def create_expense(expense_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cadastra uma nova entrada ou saída financeira para um usuário específico.

    Faz uma requisição POST assíncrona para a API de entrada ou saída financeira com os dados fornecidos.

    Args:
        expense_data (Dict[str, Any]): Um dicionário contendo os detalhes da nova entrada ou saída financeira,
                                incluindo descricao, categoria, valor (como número), tipo, data e userId.

    Returns:
        Dict[str, Any]: Um dicionário contendo os dados da entrada ou saída financeira que foi cadastrada.
    """
    url = "https://back-aprofunda-chat-despesa.onrender.com/despesas"
    
    required_fields = ["descricao", "categoria", "valor", "tipo", "data", "userId"]
    for field in required_fields:
        if field not in expense_data or not expense_data[field]:
            raise ValueError(f"Campo '{field}' é obrigatório para criar uma despesa.")


    if not isinstance(expense_data['tipo'], str) or expense_data['tipo'] not in ["entrada", "saida"]:
        raise ValueError("O campo 'tipo' deve ser 'entrada' ou 'saida'.")

    if 'valor' in expense_data and isinstance(expense_data['valor'], str):
        try:
            expense_data['valor'] = float(expense_data['valor'])
        except ValueError:
            raise ValueError("O campo 'valor' deve ser um número ou uma string numérica válida.")
    elif not isinstance(expense_data['valor'], (int, float)):
        raise ValueError("O campo 'valor' deve ser um número.")

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=expense_data)
        response.raise_for_status()
        return response.json()
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)